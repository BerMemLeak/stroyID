"""Assemble real source PDFs and generated forms into one portable PDF."""
from __future__ import annotations
import base64
import html
import io
import os
import re
import tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from PySide6.QtCore import QMarginsF, QUrl
from PySide6.QtGui import QFont, QImage, QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from word_templates import fill_docx, convert_docx_batch


def render_html(body, target, *, landscape=False):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(target))
    printer.setResolution(144)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait,
        QMarginsF(18, 16, 15, 16), QPageLayout.Unit.Millimeter))
    doc = QTextDocument()
    doc.documentLayout().setPaintDevice(printer)
    doc.setPageSize(printer.pageRect(QPrinter.Unit.DevicePixel).size())
    doc.setDefaultFont(QFont('Times New Roman', 11))
    doc.setDefaultStyleSheet('body{font-family:"Times New Roman";font-size:11pt;} '
        'h1{font-size:18pt;text-align:center;} h2{font-size:14pt;text-align:center;} '
        '.c,.pc{text-align:center;} .small,.pc{font-size:8pt;} '
        '.pl{margin-bottom:4px;} th{font-weight:bold;} td,th{padding:5px;}')
    # Images are stored in SQLite as data URLs. Never load external/local image paths.
    def image_resource(match):
        tag = match.group(0)
        source = re.search(r'src\s*=\s*([\"\'])(.*?)\1', tag, re.I | re.S)
        if source is None:
            raise ValueError('Изображение без источника')
        src = html.unescape(source.group(2))
        if not src.startswith('data:image/'):
            raise ValueError('Изображение недоступно: загрузите фотографию в карточку')
        try:
            header, data = src.split(',', 1)
            if ';base64' not in header:
                raise ValueError('Неверный формат изображения')
            image = QImage.fromData(base64.b64decode(data, validate=True))
        except Exception as exc:
            raise ValueError('Не удалось прочитать изображение') from exc
        if image.isNull():
            raise ValueError('Повреждена фотография или подпись')
        url = QUrl('stroiid-image-' + str(len(resources)))
        resources.append(url)
        doc.addResource(QTextDocument.ResourceType.ImageResource, url, image)
        def bound(name, default):
            value = re.search(name + r'\s*=\s*[\"\'](\d+)[\"\']', tag, re.I)
            return int(value.group(1)) if value else default
        scale = min(bound('width', 540) / image.width(), bound('height', 320) / image.height())
        return '<img src="' + url.toString() + '" width="' + str(round(image.width() * scale)) + \
            '" height="' + str(round(image.height() * scale)) + '">'
    resources = []
    body = re.sub(r'<img\b[^>]*>', image_resource, body, flags=re.I | re.S)
    doc.setHtml('<html><body>' + body + '</body></html>')
    doc.print_(printer)
    del doc, printer  # release Windows file handles before reading the PDF
    return Path(target).read_bytes()


def read_pdf(data, label):
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ValueError('PDF защищён паролем; загрузите открытую копию')
        if not len(reader.pages):
            raise ValueError('В PDF нет страниц')
        return reader
    except Exception as exc:
        raise ValueError(label + ': ' + str(exc)) from exc


class ExportSourceError(ValueError):
    def __init__(self, issues):
        self.details=issues
        super().__init__('Комплект не собран. Исправьте источники:\n\n'+'\n\n'.join(
            issue['location']+'\n'+issue['message']+('\nКарточка: '+issue['cardPath'] if issue.get('cardPath') else '')
            for issue in issues))


def word_template_path(store, item):
    if item.get('builtinTemplate'):
        if item['builtinTemplate'] != 'quantity':
            raise ValueError('Неизвестный встроенный шаблон')
        return Path(__file__).parent / 'ui/reference-templates/quantities.docx'
    return store.asset_path(item.get('templateKey', ''))[0]


def replace_page_refs(value, replacements):
    if isinstance(value, str):
        for marker, count in replacements.items():
            value = value.replace(marker, str(count))
        return value
    if isinstance(value, dict):
        return {key: replace_page_refs(part, replacements) for key, part in value.items()}
    if isinstance(value, list):
        return [replace_page_refs(part, replacements) for part in value]
    return value


def prepare_export(store, plan):
    """Resolve every source before offering Save; missing documents never get skipped."""
    if not isinstance(plan, dict) or not plan.get('volumes'):
        raise ValueError('Не выбран комплект ИД')
    volumes, errors = [], []
    with tempfile.TemporaryDirectory(prefix='stroiid-pdf-') as work:
        work = Path(work)
        word_jobs, word_documents = [], []
        for vi, volume in enumerate(plan['volumes']):
            docs = []
            for di, item in enumerate(volume.get('documents', [])):
                label = str(item.get('name') or item.get('type') or 'Документ')
                try:
                    kind = item.get('kind')
                    if kind == 'registry':
                        if item.get('templateKey'):
                            source, _ = store.asset_path(item['templateKey'])
                            # Validate the complete template now, before starting Word or Save.
                            fill_docx(source.read_bytes(), work / f'reg-check-{vi}-{di}.docx',
                                      item.get('values', {}), {'Реестр': []})
                        docs.append(dict(item, count=1, reader=None, selection=None))
                        continue
                    if kind == 'word':
                        source = word_template_path(store, item)
                        filled = work / f'word-{vi}-{di}.docx'
                        target = filled.with_suffix('.pdf')
                        fill_docx(source.read_bytes(), filled, item.get('values', {}), item.get('collections', {}))
                        doc = dict(item, count=1, reader=None, selection=None)
                        docs.append(doc)
                        word_jobs.append((filled, target))
                        word_documents.append((doc, target, label))
                        continue
                    if kind == 'pdf':
                        if not item.get('key'):
                            raise ValueError('исходный PDF не загружен; откройте карточку и загрузите файл')
                        source, _ = store.asset_path(item['key'])
                        reader = read_pdf(source.read_bytes(), label)
                        selection = list(range(len(reader.pages)))
                        if item.get('from') is not None or item.get('to') is not None:
                            first, last = item.get('from'), item.get('to')
                            if (type(first) is not int or type(last) is not int
                                    or first < 1 or last < first or last > len(reader.pages)):
                                raise ValueError('выбранные листы выходят за пределы исходного PDF')
                            selection = list(range(first - 1, last))
                    elif kind == 'html':
                        pieces = item.get('parts') or [item.get('html', '')]
                        if not all(isinstance(p, str) and p.strip() for p in pieces):
                            raise ValueError('нет формы документа')
                        writer = PdfWriter()
                        for pi, piece in enumerate(pieces):
                            data = render_html(piece, work / f'{vi}-{di}-{pi}.pdf',
                                               landscape=bool(item.get('landscape')))
                            writer.append(read_pdf(data, label), import_outline=False)
                        merged = io.BytesIO()
                        writer.write(merged)
                        writer.close()
                        reader = read_pdf(merged.getvalue(), label)
                        selection = list(range(len(reader.pages)))
                    else:
                        raise ValueError(item.get('error') or 'нет доступного источника')
                    if item.get('frame'):
                        from drawing_frame import framed_reader
                        reader = framed_reader(reader, selection, item['frame'], store)
                        selection = list(range(len(reader.pages)))
                    docs.append(dict(item, count=len(selection), reader=reader, selection=selection))
                except Exception as exc:
                    errors.append({'id':item.get('id',''),'ref':item.get('sourceRef',''),
                        'location':item.get('sourceLocation') or ' → '.join([str(plan.get('object','Объект')),str(volume.get('title','Том')),str(item.get('type','Документ')),label]),
                        'message':str(exc),'cardPath':str(store.paths.get(item.get('cardKey',''),'')) if hasattr(store,'paths') else ''})
            if not docs:
                errors.append({'location':str(volume.get('title','Том')),'message':'состав пуст'})
            volumes.append({'title': str(volume.get('title', 'Том')), 'documents': docs})
        if errors:
            raise ExportSourceError(errors)
        convert_docx_batch(word_jobs)
        for doc, target, label in word_documents:
            reader = read_pdf(target.read_bytes(), label)
            count = len(reader.pages)
            doc.update(reader=reader, selection=list(range(count)), count=count)
        # Render acts again after attachments have their actual (possibly multi-page) length.
        # Only generated forms participate; signed scans remain untouched.
        jobs, updated = [], []
        for vi, volume in enumerate(volumes):
            by_id = {doc.get('id'): doc for doc in volume['documents']}
            for di, doc in enumerate(volume['documents']):
                refs = doc.get('attachmentPageRefs')
                if not refs or doc['kind'] not in ('html', 'word'):
                    continue
                missing = set(refs.values()) - set(by_id)
                if missing:
                    raise ValueError('В составе отсутствует приложение: ' + ', '.join(sorted(missing)))
                replacements = {marker: by_id[ident]['count'] for marker, ident in refs.items()}
                for key in ('values', 'collections', 'html', 'parts'):
                    if key in doc:
                        doc[key] = replace_page_refs(doc[key], replacements)
                target = work / f'act-final-{vi}-{di}.pdf'
                if doc['kind'] == 'word':
                    filled = target.with_suffix('.docx')
                    fill_docx(word_template_path(store, doc).read_bytes(), filled,
                              doc.get('values', {}), doc.get('collections', {}))
                    jobs.append((filled, target))
                else:
                    writer = PdfWriter()
                    for pi, piece in enumerate(doc.get('parts') or [doc.get('html', '')]):
                        data = render_html(piece, work / f'act-part-{vi}-{di}-{pi}.pdf',
                                           landscape=bool(doc.get('landscape')))
                        writer.append(read_pdf(data, doc.get('name', 'Акт')), import_outline=False)
                    with target.open('wb') as stream:
                        writer.write(stream)
                    writer.close()
                updated.append((doc, target))
        convert_docx_batch(jobs)
        for doc, target in updated:
            reader = read_pdf(target.read_bytes(), doc.get('name', 'Акт'))
            doc.update(reader=reader, count=len(reader.pages), selection=list(range(len(reader.pages))))
        # Actual PDF page counts drive the registry, including the registry's own length.
        for attempt in range(12):
            cursor, changed = 1, False
            for vi, volume in enumerate(volumes):
                rows = []
                for n, doc in enumerate(volume['documents'], 1):
                    doc.update(n=n, start=cursor, end=cursor + doc['count'] - 1)
                    cursor += doc['count']
                    rows.append(doc)
                for di, doc in enumerate(rows):
                    if doc['kind'] != 'registry':
                        continue
                    target = work / f'registry-{vi}-{di}.pdf'
                    if doc.get('templateKey'):
                        source, _ = store.asset_path(doc['templateKey'])
                        entries = [{'Номер': r['n'], 'Тип': r.get('type', ''),
                            'Наименование': r.get('name', ''), 'Номер_Дата': r.get('nd', ''),
                            'Листы': str(r['start']) if r['start'] == r['end'] else f"{r['start']}-{r['end']}"} for r in rows]
                        summary = '\n'.join(f"{r['Номер']}. {r['Наименование']} — листы {r['Листы']}" for r in entries)
                        values = dict(doc.get('values', {}), Реестр=summary, Содержание=summary)
                        filled = target.with_suffix('.docx')
                        fill_docx(source.read_bytes(), filled, values, {'Реестр': entries})
                        convert_docx_batch([(filled, target)])
                        data = target.read_bytes()
                    else:
                        body = registry_html(volume['title'], rows)
                        data = render_html(body, target)
                    reader = read_pdf(data, 'Реестр')
                    count = len(reader.pages)
                    changed |= count != doc['count']
                    doc.update(reader=reader, selection=list(range(count)), count=count)
            if not changed:
                break
        else:
            raise ValueError('Не удалось согласовать номера страниц реестра')
    return {'volumes': volumes, 'pages': cursor - 1,
            'documents': sum(len(v['documents']) for v in volumes), 'object': plan.get('object', '')}


def registry_html(title, rows):
    esc = lambda x: html.escape(str(x or ''))
    cells = []
    for doc in rows:
        span = str(doc['start']) if doc['start'] == doc['end'] else f"{doc['start']}-{doc['end']}"
        cells.append('<tr><td>' + str(doc['n']) + '</td><td>' + esc(doc.get('type')) +
            '<br>' + esc(doc.get('name')) + '</td><td>' + esc(doc.get('nd')) +
            '</td><td>' + span + '</td></tr>')
    return '<h2>РЕЕСТР ДОКУМЕНТОВ</h2><p align="center">' + esc(title) + \
        '</p><table border="1" cellspacing="0" cellpadding="5" width="100%">' + \
        '<thead><tr><th width="7%">№</th><th width="57%">Наименование документа</th>' + \
        '<th width="23%">Номер и дата</th><th width="13%">Листы<br>PDF</th></tr></thead>' + \
        '<tbody>' + ''.join(cells) + '</tbody></table>'


def write_export(prepared, target, store):
    target = Path(target).resolve()
    # Never let an export replace the live database or a managed original.
    if target == store.root or store.root in target.parents:
        raise ValueError('Сохраните итоговый PDF вне папки служебных данных СтройИД')
    writer = PdfWriter()
    try:
        for volume in prepared['volumes']:
            parent = writer.add_outline_item(volume['title'], len(writer.pages))
            for doc in volume['documents']:
                start = len(writer.pages)
                writer.append(doc['reader'], pages=doc['selection'], import_outline=False)
                writer.add_outline_item(str(doc.get('name') or doc.get('type')), start, parent=parent)
        writer.add_metadata({'/Title': str(prepared['object']) + ' - Исполнительная документация',
                             '/Creator': 'СтройИД Desktop 0.9.4'})
        handle, name = tempfile.mkstemp(prefix='.stroiid-', suffix='.pdf', dir=target.parent)
        try:
            with os.fdopen(handle, 'wb') as output:
                writer.write(output)
                output.flush()
                os.fsync(output.fileno())
            check = read_pdf(Path(name).read_bytes(), 'Итоговый PDF')
            if len(check.pages) != prepared['pages']:
                raise ValueError('Число страниц итогового PDF не совпало с реестром')
            os.replace(name, target)
        finally:
            Path(name).unlink(missing_ok=True)
    finally:
        writer.close()
    return {'path': str(target), 'pages': prepared['pages'], 'documents': prepared['documents']}
