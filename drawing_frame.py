"""Physical-size vector frame. ГОСТ Р 21.101-2026, Е форма 3, Ж рисунок Ж.1."""
from __future__ import annotations
import base64, html, io, re, tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from PySide6.QtCore import QByteArray, QMarginsF, QRectF, QSize, QSizeF, QBuffer, QIODevice
from PySide6.QtGui import QPageSize, QPainter, QPdfWriter, QImage, QFont, QFontMetricsF, QFontDatabase
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtPdf import QPdfDocument

TEMPLATE=Path(__file__).parent/'ui'/'frame-templates'/'gost-form3.html'
MM=72/25.4
FRAME_SIGNER_LIMIT=6


def frame_signer_values(config, values):
    """Populate the six physical slots; legacy exports keep their original cells."""
    rows=config.get('signerRows')
    if rows is None:
        rows=[{'role':'Разработал','name':values.get('Разработал','')},
              {'role':'Проверил','name':values.get('Проверил','')}, {}, {},
              {'role':'Н. контр.','name':values.get('Нормоконтроль','')}]
    if not isinstance(rows,list) or len(rows)>FRAME_SIGNER_LIMIT:
        raise ValueError(f'В штампе доступно не более {FRAME_SIGNER_LIMIT} строк подписантов')
    for i in range(FRAME_SIGNER_LIMIT):
        row=rows[i] if i<len(rows) else {}
        if not isinstance(row,dict) or not all(isinstance(row.get(key,''),str) for key in ('role','name')):
            raise ValueError('Некорректная строка подписанта рамки')
        role,name=row.get('role','').strip(),row.get('name','').strip()
        values[f'Роль_{i+1}']=role
        values[f'Подписант_{i+1}']=name
        values[f'Дата_Подписанта_{i+1}']=values.get('Дата','') if role or name else ''
    return values


SHEET_CAPTION_SVG = (
    '<text id="drawing-sheet-caption" x="{{X_Центр_Листа}}" y="{{Y_Центр_Листа}}" '
    'font-size="5" text-anchor="middle" fill="black" stroke="none" '
    'data-text-scale="0.75" data-fit-width="{{Ширина_Надписи_Листа}}" '
    'data-fit-height="40">{{Надпись_Схемы}}</text>'
)


def frame_sheet_values(config, sheet, values):
    """Use source sheet numbers and explicit per-sheet places, never the act place."""
    values['Номер_Схемы_Листа']=''
    values['Место_Выполнения_Листа']=''
    values['Надпись_Схемы']=''
    if not config.get('captionEnabled'):
        return values
    places=config.get('sheetPlaces',{})
    if not isinstance(places,dict):
        raise ValueError('Места выполнения по листам должны быть заданы по номерам листов')
    place=places.get(str(sheet),'')
    if not isinstance(place,str):
        raise ValueError('Место выполнения листа должно быть текстом')
    base=str(values.get('Номер_Схемы','') or '').strip()
    number=f'{base}.{sheet}' if base else str(sheet)
    work=str(values.get('Наименование_Работ','') or '').strip()
    description=' '.join(part for part in (work,place.strip()) if part)
    values['Номер_Схемы_Листа']=number
    values['Место_Выполнения_Листа']=place.strip()
    values['Надпись_Схемы']='Исполнительная схема № '+number+(f' «{description}»' if description else '')
    return values


def resolve_frame_font(config, store=None):
    """Never silently substitute the requested production drafting font."""
    if config.get('fontKey') and store:
        path, _ = store.asset_path(config['fontKey'])
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            raise ValueError('Не удалось загрузить шрифт рамки')
    family = next((f for f in QFontDatabase.families() if f.casefold() == 'isocpeur'), None)
    if family:
        return family
    if config.get('requireFont'):
        raise ValueError('ISOCPEUR не найден. Выберите файл шрифта в настройках рамки (Профили и шаблоны → Исполнительные схемы).')
    return 'DejaVu Sans'  # Legacy/template validation and geometry tests only.

def template_svg(template, values, font_family=None):
    if len(template)>500_000: raise ValueError('Шаблон рамки слишком большой')
    match=re.search(r'<svg\b[\s\S]*?</svg>',template,re.I)
    if not match: raise ValueError('HTML-шаблон должен содержать один SVG с рамкой')
    svg=match.group(0)
    if re.search(r'<\s*(script|foreignObject|image|use)\b|\bon\w+\s*=|(?:href|url\s*\()|<!ENTITY',svg,re.I):
        raise ValueError('В рамке допустимы только локальные векторные элементы и текст')
    tags=set(re.findall(r'\{\{([^{}]+)\}\}',svg))
    unknown=tags-values.keys()
    if unknown: raise ValueError('Неизвестные теги рамки: '+', '.join(sorted(unknown)))
    svg=re.sub(r'\{\{([^{}]+)\}\}',lambda m:html.escape(str(values[m[1]]),quote=True),svg)
    # Fit populated fields inside their physical cells, including long object names.
    import xml.etree.ElementTree as ET
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    tree=ET.fromstring(svg)
    family=font_family or tree.get('font-family','ISOCPEUR');tree.set('font-family',family)
    font=QFont(family);font.setPixelSize(100);metrics=QFontMetricsF(font)
    # QtSvg rounds small font sizes and ignores absolute positioning on tspans.
    # Render each line as its own text node at a large font size, transformed
    # back to physical mm. This preserves fractional sizes and line positions.
    parents = {child: parent for parent in tree.iter() for child in parent}
    ns = '{http://www.w3.org/2000/svg}'
    for node in list(tree.iter()):
        if node.tag != ns+'text' or len(node) or not (node.text or '').strip():
            continue
        limit = node.attrib.pop('data-fit-width', None)
        height = node.attrib.pop('data-fit-height', None)
        stretch = float(node.attrib.pop('data-text-scale', '1'))
        if not node.text:
            continue
        text = node.text.strip()
        ancestor=node
        while 'font-size' not in ancestor.attrib and ancestor in parents:
            ancestor=parents[ancestor]
        raw_size=ancestor.get('font-size', '3')
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', raw_size):
            continue  # Keep user-authored SVG/CSS sizes and nested text intact.
        size = float(raw_size)
        lines = [text]
        if limit:
            if height:
                for candidate in dict.fromkeys((size, min(size, 3.5))):
                    lines=[];line=''
                    for word in text.split():
                        proposed=(line+' '+word).strip()
                        if line and metrics.horizontalAdvance(proposed)/100*candidate*stretch > float(limit):
                            lines.append(line);line=word
                        else:line=proposed
                    if line:lines.append(line)
                    if len(lines)*candidate*1.2 <= float(height):break
                size=candidate
                if any(metrics.horizontalAdvance(line)/100*size*stretch > float(limit) for line in lines) or len(lines)*size*1.2 > float(height):
                    raise ValueError('Текст не помещается в графу основной надписи: '+text)
            else:
                width=metrics.horizontalAdvance(text)/100*size*stretch
                if width>float(limit):size*=float(limit)/width
        parent=parents[node];position=list(parent).index(node)
        x=float(node.get('x','0'));y=float(node.get('y','0'))
        original_transform=node.get('transform','')
        first=y-(len(lines)-1)*size*1.2/2
        parent.remove(node)
        for i,line in enumerate(lines):
            attrs={k:v for k,v in node.attrib.items() if k not in ('x','y','font-size','transform')}
            attrs['font-size']='100'
            attrs['transform']=f'{original_transform} translate({x} {first+i*size*1.2}) scale({size/100*stretch} {size/100})'.strip()
            rendered=ET.Element(ns+'text',attrs);rendered.text=line
            parent.insert(position+i,rendered)
    return ET.tostring(tree,encoding='utf-8')

def frame_page(page, config, *, sheet=1, total=1, template=None):
    # Normalize PDF rotation and crop origin without rescaling the original drawing.
    from pypdf import Transformation
    page.transfer_rotation_to_content()
    crop=page.cropbox
    w,h=float(crop.width),float(crop.height)
    if w/MM<210-1 or h/MM<120: raise ValueError('Лист слишком мал для основной надписи 185 × 55 мм')
    if float(crop.left) or float(crop.bottom):
        page.add_transformation(Transformation().translate(-float(crop.left),-float(crop.bottom)))
    from pypdf.generic import RectangleObject
    page.mediabox=RectangleObject([0,0,w,h]);page.cropbox=RectangleObject([0,0,w,h])
    wm,hm=w/MM,h/MM
    # A frame is an overlay only. Ignore legacy fitContent settings so existing
    # cards cannot accidentally scale or relocate the source drawing.
    values={**config.get('values',{}),'Ширина':wm,'Высота':hm,'X_Надпись':wm-190,'Y_Надпись':hm-60,
        'X_Приложение':wm-58,'Y_Инвентарных_Граф':hm-90,'X_Формат':wm-5,'Y_Формат':hm-1.5,'Ширина_Рамки':wm-25,'Высота_Рамки':hm-10,'Лист':str(sheet),
        'Листов':str(total), 'Формат':paper_format(wm,hm),
        'X_Центр_Листа':wm/2, 'Y_Центр_Листа':hm/2, 'Ширина_Надписи_Листа':min(wm-40,240)}
    for key in ('Шифр','Объект','Здание','Название_Схемы','Организация','Разработал','Проверил','Нормоконтроль','Дата','Стадия','АОСР','Работы','Система','Выполнение','Дата_Акта','Номер_Приложения'):
        values.setdefault(key,'')
    values['Приложение']=values.get('Номер_Приложения','')
    values.setdefault('Основание_Приложения', 'К акту №' if values['АОСР'] else 'К разделу')
    values.setdefault('Шифр_Приложения', values['АОСР'])
    values.setdefault('Дата_Приложения', values['Дата_Акта'])
    frame_signer_values(config,values)
    frame_sheet_values(config,sheet,values)
    source=template or TEMPLATE.read_text('utf-8')
    if template and config.get('signerRows') is not None:
        # Old custom SVGs hard-code roles and cannot represent ordered custom
        # rows. Require matching slots instead of silently printing wrong people.
        for i,row in enumerate(config['signerRows'],1):
            if not row.get('role','').strip() and not row.get('name','').strip():
                continue
            if any('{{'+key+'_'+str(i)+'}}' not in source for key in ('Роль','Подписант')):
                raise ValueError('HTML-шаблон рамки не поддерживает выбранные строки. '
                                 'Используйте встроенный шаблон или добавьте теги {{Роль_'+str(i)+'}} и {{Подписант_'+str(i)+'}}.')
    if values['Надпись_Схемы'] and '{{Надпись_Схемы}}' not in source:
        source=re.sub(r'</svg\s*>',lambda m:SHEET_CAPTION_SVG+m.group(0),source,count=1,flags=re.I)
    svg=template_svg(source,values,config.get('_resolvedFont') or resolve_frame_font(config))
    renderer=QSvgRenderer(QByteArray(svg))
    if not renderer.isValid(): raise ValueError('Некорректный SVG рамки')
    with tempfile.TemporaryDirectory(prefix='sid-frame-') as tmp:
        target=Path(tmp)/'frame.pdf'
        writer=QPdfWriter(str(target));writer.setResolution(720)
        writer.setPageSize(QPageSize(QSizeF(wm,hm),QPageSize.Unit.Millimeter))
        writer.setPageMargins(QMarginsF(0,0,0,0))
        painter=QPainter(writer);renderer.render(painter,QRectF(0,0,writer.width(),writer.height()));painter.end();del painter,writer
        overlay=PdfReader(io.BytesIO(target.read_bytes())).pages[0]
        # Quantization of Qt paper dimensions must never resize the imported content.
        page.merge_page(overlay,expand=False)
    return page

def paper_format(w,h):
    for name,a,b in [('A4',210,297),('A3',297,420),('A2',420,594),('A1',594,841),('A0',841,1189)]:
        if abs(min(w,h)-a)<1 and abs(max(w,h)-b)<1:return name
    return f'{w:.1f} × {h:.1f} мм'

def framed_reader(reader, selection, config, store):
    template=None
    if config.get('templateKey'):
        path,_=store.asset_path(config['templateKey']);template=path.read_text('utf-8-sig')
    config = {**config, '_resolvedFont': resolve_frame_font(config, store)}
    writer=PdfWriter()
    for index in selection:
        # Import a clone before normalizing; other uses of the source remain untouched.
        writer.add_page(reader.pages[index])
        frame_page(writer.pages[-1],config,sheet=index+1,total=len(reader.pages),template=template)
    buf=io.BytesIO();writer.write(buf);writer.close()
    return PdfReader(io.BytesIO(buf.getvalue()))

def preview(store, params):
    path,_=store.asset_path(params['key']);reader=PdfReader(path)
    page=int(params.get('page',1))
    if page<1 or page>len(reader.pages):raise ValueError('Лист вне диапазона PDF')
    if params.get('frame'):
        rendered=framed_reader(reader,[page-1],params['frame'],store)
    else:
        writer=PdfWriter();writer.add_page(reader.pages[page-1]);b=io.BytesIO();writer.write(b);writer.close();rendered=PdfReader(io.BytesIO(b.getvalue()))
    b=io.BytesIO();writer=PdfWriter();writer.append(rendered);writer.write(b);writer.close()
    # QtPdf can retain its file handle after close() on Windows. Keep the PDF
    # and the resulting PNG in memory so cleanup cannot encounter WinError 32.
    pdf_buffer=QBuffer();pdf_buffer.setData(QByteArray(b.getvalue()))
    pdf_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    doc=QPdfDocument()
    try:
        doc.load(pdf_buffer)
        if doc.error()!=QPdfDocument.Error.None_ or doc.pageCount()!=1:
            raise ValueError('Не удалось открыть PDF для предпросмотра')
        size=doc.pagePointSize(0);scale=min(1400/size.width(),1800/size.height());image=doc.render(0,QSize(round(size.width()*scale),round(size.height()*scale)))
        if image.isNull():raise ValueError('Не удалось отрисовать лист PDF')
        white=QImage(image.size(),QImage.Format.Format_RGB32);white.fill(0xffffffff)
        painter=QPainter(white);painter.drawImage(0,0,image);painter.end()
        png_buffer=QBuffer();png_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        try:
            if not white.save(png_buffer,'PNG'):
                raise ValueError('Не удалось подготовить изображение предпросмотра')
            encoded=base64.b64encode(bytes(png_buffer.data())).decode()
        finally:
            png_buffer.close()
        return {'image':'data:image/png;base64,'+encoded,'pages':len(reader.pages),'width':round(size.width()/MM,2),'height':round(size.height()/MM,2)}
    finally:
        doc.close()
        del doc
        pdf_buffer.close()
