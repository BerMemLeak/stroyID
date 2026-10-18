"""Physical-size vector frame. ГОСТ Р 21.101-2026, Е форма 3, Ж рисунок Ж.1."""
from __future__ import annotations
import base64, html, io, re, tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from PySide6.QtCore import QByteArray, QMarginsF, QRectF, QSize, QSizeF, QBuffer, QIODevice
from PySide6.QtGui import QPageSize, QPainter, QPdfWriter, QImage, QFont, QFontMetricsF
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtPdf import QPdfDocument

TEMPLATE=Path(__file__).parent/'ui'/'frame-templates'/'gost-form3.html'
MM=72/25.4

def template_svg(template, values):
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
    font=QFont('Arial');font.setPixelSize(100);metrics=QFontMetricsF(font)
    for node in tree.iter():
        limit=node.attrib.pop('data-fit-width', None)
        if limit and node.text:
            size=float(node.get('font-size','3'));width=metrics.horizontalAdvance(node.text)/100*size
            if width>float(limit):node.set('font-size',str(size*float(limit)/width))
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
    values={**config.get('values',{}),'Ширина':wm,'Высота':hm,'X_Надпись':wm-190,'Y_Надпись':hm-60,
        'Y_Инвентарных_Граф':hm-90,'X_Формат':wm-5,'Y_Формат':hm-1.5,'Ширина_Рамки':wm-25,'Высота_Рамки':hm-10,'Лист':str(sheet) if total>1 else '',
        'Листов':str(total) if sheet==1 else '', 'Формат':paper_format(wm,hm)}
    for key in ('Шифр','Объект','Здание','Название_Схемы','Организация','Разработал','Проверил','Нормоконтроль','Дата','Стадия','АОСР','Работы','Система','Выполнение'):
        values.setdefault(key,'')
    svg=template_svg(template or TEMPLATE.read_text('utf-8'),values)
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
