"""Preserve a user's DOCX layout while filling tags; Word performs PDF conversion."""
from __future__ import annotations
import base64
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
TAG = re.compile(r'\{\{\s*([^{}]+?)\s*\}\}')
PART = re.compile(r'^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$')

def parse_xml(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Неподдерживаемая структура Word-файла')
    for _, ns in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
        try:
            ET.register_namespace(*ns)
        except ValueError:
            pass
    return ET.fromstring(data)


def serialize_xml(root, original):
    # Word's mc:Ignorable lists namespace prefixes as attribute text. ElementTree
    # omits unused declarations; retain them so ordinary Word files stay valid.
    namespaces = dict(ns for _, ns in ET.iterparse(io.BytesIO(original), events=('start-ns',)))
    for prefix, uri in namespaces.items():
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass
    data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    opening = re.search(rb'<(?!\?)[^>]+>', data)
    tag = opening.group(0)
    for prefix, uri in namespaces.items():
        attribute = ('xmlns:' + prefix if prefix else 'xmlns').encode()
        if re.search(rb'\b' + re.escape(attribute) + rb'=', tag):
            continue
        import html
        declaration = b' ' + attribute + b'="' + html.escape(uri, quote=True).encode() + b'"'
        tag = tag[:-1] + declaration + b'>'
    return data[:opening.start()] + tag + data[opening.end():]

def package(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 4000 or sum(x.file_size for x in entries) > 100 * 1024**2:
                raise ValueError('Шаблон превышает допустимый размер 100 МБ')
            if len({x.filename for x in entries}) != len(entries):
                raise ValueError('Повторяющиеся части Word-файла')
            content = {x.filename: archive.read(x) for x in entries}
        if 'word/document.xml' not in content or '[Content_Types].xml' not in content:
            raise ValueError('Выберите документ Word в формате .docx')
        if any('vbaproject' in x.lower() for x in content):
            raise ValueError('Загрузите шаблон .docx без макросов')
        for name, body in content.items():
            if name.endswith('.rels'):
                for rel in parse_xml(body):
                    if rel.get('TargetMode') == 'External' and not rel.get('Type', '').endswith('/hyperlink'):
                        raise ValueError('Вставьте внешние изображения и вложения внутрь Word-файла')
        return content
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        raise ValueError('Повреждён Word-файл или выбран неверный формат') from exc

def paragraph_text(paragraph):
    return ''.join(t.text or '' for t in paragraph.iter('{' + W + '}t'))

def inspect_docx(data):
    parts = package(data)
    tags = set()
    for name, body in parts.items():
        if PART.match(name):
            root = parse_xml(body)
            for paragraph in root.iter('{' + W + '}p'):
                tags.update(m.group(1).strip() for m in TAG.finditer(paragraph_text(paragraph)))
    return {'tags': sorted(tags), 'size': len(data)}

def replace_text(paragraph, values):
    """Replace split-run tags backwards, keeping surrounding formatting and text."""
    nodes = list(paragraph.iter('{' + W + '}t'))
    text = ''.join(t.text or '' for t in nodes)
    offsets, position = [], 0
    for node in nodes:
        size = len(node.text or '')
        offsets.append((position, position + size))
        position += size
    for match in reversed(list(TAG.finditer(text))):
        key = match.group(1).strip()
        if key not in values:
            raise ValueError('Неизвестный тег {{' + key + '}}')
        value = str(values[key] if values[key] is not None else '')
        hits = [i for i, (a, b) in enumerate(offsets) if a < match.end() and b > match.start()]
        if not hits:
            continue
        first, last = hits[0], hits[-1]
        left = (nodes[first].text or '')[:match.start() - offsets[first][0]]
        right = (nodes[last].text or '')[match.end() - offsets[last][0]:]
        nodes[first].text = left + value + (right if first == last else '')
        nodes[first].set(XML_SPACE, 'preserve')
        for i in hits[1:]:
            nodes[i].text = right if i == last else ''
            nodes[i].set(XML_SPACE, 'preserve')
    # Word requires explicit break/tab elements, not literal control characters in w:t.
    parents = {child: parent for parent in paragraph.iter() for child in parent}
    for node in nodes:
        value = node.text or ''
        if '\n' not in value and '\t' not in value and '\r' not in value:
            continue
        parent = parents[node]
        index = list(parent).index(node)
        parent.remove(node)
        for segment in re.split(r'(\n|\t)', value.replace('\r\n', '\n').replace('\r', '\n')):
            if not segment:
                continue
            new = ET.Element('{' + W + '}' + ('br' if segment == '\n' else 'tab' if segment == '\t' else 't'))
            if segment not in ('\n', '\t'):
                new.text = segment
                new.set(XML_SPACE, 'preserve')
            parent.insert(index, new)
            index += 1


def add_picture(paragraph, value, parts, part_name, width_inches=5.2):
    if not isinstance(value, str) or not re.match(r'^data:image/(png|jpeg);base64,', value):
        raise ValueError('Фото не загружено или имеет неподдерживаемый формат')
    header, encoded = value.split(',', 1)
    try:
        data = base64.b64decode(encoded, validate=True)
        from PySide6.QtGui import QImage
        img = QImage.fromData(data)
        if img.isNull():
            raise ValueError('Повреждено фото')
    except Exception as exc:
        raise ValueError('Не удалось прочитать фото') from exc
    ext = 'png' if '/png;' in header else 'jpeg'
    unique = uuid.uuid4().hex
    name = 'stroiid-' + unique + '.' + ext
    parts['word/media/' + name] = data
    rel_name = 'word/_rels/' + Path(part_name).name + '.rels'
    rels = parse_xml(parts[rel_name]) if rel_name in parts else ET.Element('{' + PKG + '}Relationships')
    rid = 'rIdStroyID' + unique
    ET.SubElement(rels, '{' + PKG + '}Relationship', {'Id': rid, 'Type': R + '/image', 'Target': 'media/' + name})
    parts[rel_name] = ET.tostring(rels, encoding='utf-8', xml_declaration=True)
    types = parse_xml(parts['[Content_Types].xml'])
    ct = 'http://schemas.openxmlformats.org/package/2006/content-types'
    if not any(x.get('Extension') == ext for x in types):
        ET.SubElement(types, '{' + ct + '}Default', {'Extension': ext, 'ContentType': 'image/' + ext})
    parts['[Content_Types].xml'] = ET.tostring(types, encoding='utf-8', xml_declaration=True)
    # Fit an image in an A4 portrait document, with its original proportions.
    scale = min(width_inches * 914400 / img.width(), 3.4 * 914400 / img.height())
    cx, cy = round(img.width() * scale), round(img.height() * scale)
    wp = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
    a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    pic = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
    drawing = ET.fromstring(f'''<w:r xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="{wp}" xmlns:a="{a}" xmlns:pic="{pic}"><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{int(unique[:7],16)}" name="Фото"/><a:graphic><a:graphicData uri="{pic}"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>''')
    paragraph.append(drawing)


def fill_docx(data, target, values, collections=None):
    from document_tags import collection_tags, validate_values
    parts = package(data)
    collections = collections or {}
    known = set(values)
    for key, rows in collections.items():
        for row in rows:
            known.update(key + '.' + str(k) for k in row)
    known.update(collection_tags())
    missing = set(inspect_docx(data)['tags']) - known
    if missing:
        raise ValueError('Неизвестные теги: ' + ', '.join('{{' + x + '}}' for x in sorted(missing)))
    validate_values(inspect_docx(data)['tags'], values)
    logo = values.get('Комплект.Логотип', '')
    logo_tag_present = 'Комплект.Логотип' in inspect_docx(data)['tags']
    text_values = {**values, 'Комплект.Логотип': ''}
    for name in list(parts):
        if not PART.match(name):
            continue
        root = parse_xml(parts[name])
        processed = set()
        # A row containing collection tags is the repeatable sample row.
        for table in list(root.iter('{' + W + '}tbl')):
            for row in list(table):
                if row.tag != '{' + W + '}tr':
                    continue
                tags = [m.group(1).strip() for p in row.iter('{' + W + '}p') for m in TAG.finditer(paragraph_text(p))]
                groups = {x.split('.')[0] for x in tags if x in collection_tags()}
                if not groups:
                    continue
                if len(groups) != 1:
                    raise ValueError('В одной строке таблицы используйте теги одного списка')
                group = groups.pop()
                pos = list(table).index(row)
                table.remove(row)
                for row_values in collections.get(group, []):
                    new_row = copy.deepcopy(row)
                    cells = list(new_row.findall('{' + W + '}tc'))
                    merged = dict(values, **{group + '.' + str(k): v for k, v in row_values.items()})
                    for paragraph in new_row.iter('{' + W + '}p'):
                        has_photo = bool(re.search(r'\{\{\s*Фото\.Изображение\s*\}\}', paragraph_text(paragraph)))
                        local = dict(merged)
                        if has_photo:
                            local['Фото.Изображение'] = ''
                        replace_text(paragraph, local)
                        processed.add(id(paragraph))
                        if has_photo:
                            cell = next((c for c in cells if paragraph in list(c.iter())), None)
                            cell_width = cell.find('{' + W + '}tcPr/{' + W + '}tcW') if cell is not None else None
                            width = 5.2 / max(len(cells), 1)
                            if cell_width is not None and cell_width.get('{' + W + '}type') == 'dxa':
                                width = min(5.2, max(.5, (int(cell_width.get('{' + W + '}w', '0')) - 160) / 1440))
                            add_picture(paragraph, row_values.get('Изображение'), parts, name, width)
                    table.insert(pos, new_row)
                    pos += 1
        for paragraph in root.iter('{' + W + '}p'):
            if id(paragraph) not in processed:
                has_logo = bool(re.search(r'\{\{\s*Комплект\.Логотип\s*\}\}', paragraph_text(paragraph)))
                replace_text(paragraph, text_values)
                if has_logo and logo:
                    add_picture(paragraph, logo, parts, name, 1.5)
        if name == 'word/document.xml' and logo and not logo_tag_present:
            body = root.find('{' + W + '}body')
            paragraph = ET.Element('{' + W + '}p')
            props = ET.SubElement(paragraph, '{' + W + '}pPr')
            ET.SubElement(props, '{' + W + '}jc', {'{' + W + '}val': 'right'})
            add_picture(paragraph, logo, parts, name, 1.5)
            body.insert(0, paragraph)
        parts[name] = serialize_xml(root, parts[name])
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, body in parts.items():
            archive.writestr(name, body)
    return target


WORD_SCRIPT = r'''param([string]$Manifest)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$word=$null; $documents=$null; $document=$null; $failed=$false; $sourceName=''
try {
    $jobs=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($Manifest, [Text.Encoding]::UTF8))
    $word=New-Object -ComObject Word.Application
    $word.Visible=$false; $word.DisplayAlerts=0; $word.AutomationSecurity=3
    $documents=$word.Documents
    foreach ($job in $jobs) {
        if ($job.source -isnot [string] -or $job.target -isnot [string]) { throw 'Invalid Word conversion job: source and target must be single paths' }
        $sourceName=[IO.Path]::GetFullPath($job.source)
        if (!(Test-Path -LiteralPath $sourceName -PathType Leaf)) { throw ('Source does not exist: '+$sourceName) }
        try {
            for ($attempt=0; $attempt -lt 3; $attempt++) {
                try {
                    $document=$documents.Open($sourceName,$false,$true,$false)
                    if ($null -eq $document) { throw 'Word returned an empty document reference' }
                    $document.Repaginate()
                    $document.ExportAsFixedFormat([string]$job.target,17)
                    break
                } catch {
                    if ($null -ne $document) {
                        try { $document.Close(0) } catch {}
                        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) } catch {}
                        $document=$null
                    }
                    if ($attempt -eq 2) { throw }
                    Start-Sleep -Milliseconds 600
                }
            }
        } finally {
            if ($null -ne $document) {
                try { $document.Close(0) } catch {}
                try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) } catch {}
                $document=$null
            }
        }
    }
} catch {
    $failed=$true
    [Console]::Error.WriteLine('Document: '+$sourceName)
    [Console]::Error.WriteLine($_.Exception.ToString())
} finally {
    if ($null -ne $documents) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($documents) } catch {}
        $documents=$null
    }
    if ($null -ne $word) {
        try { $word.Quit(0) } catch {}
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) } catch {}
        $word=$null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
if ($failed) { exit 1 }
exit 0
''' 


def word_executable():
    if sys.platform != 'win32':
        raise ValueError('Открытие в Microsoft Word доступно на Windows')
    import winreg
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE', 0, winreg.KEY_READ | view) as key:
                    value = winreg.QueryValueEx(key, '')[0].strip('"')
                if Path(value).is_file():
                    return value
            except OSError:
                pass
    raise ValueError('Microsoft Word не найден. Установите Word и откройте его один раз.')


def open_in_word(path):
    subprocess.Popen([word_executable(), str(Path(path).resolve())], close_fds=True)
    return True


def convert_docx_batch(jobs):
    """Run only the installed Word; no lossy HTML substitution for DOCX."""
    if not jobs:
        return
    if sys.platform != 'win32':
        raise ValueError('Для преобразования Word-шаблонов в PDF нужен Microsoft Word на Windows')
    with tempfile.TemporaryDirectory(prefix='stroiid-word-') as folder:
        folder = Path(folder)
        script, manifest = folder / 'export.ps1', folder / 'jobs.json'
        script.write_text(WORD_SCRIPT, encoding='utf-8-sig')
        manifest.write_text(json.dumps([{'source': str(Path(a).resolve()), 'target': str(Path(b).resolve())} for a, b in jobs], ensure_ascii=False), encoding='utf-8')
        with (folder / 'output.log').open('wb') as output:
            process = subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-STA',
                '-ExecutionPolicy', 'Bypass', '-File', str(script), str(manifest)], stdout=output,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            end = time.monotonic() + max(180, 30 * len(jobs))
            while process.poll() is None:
                if time.monotonic() > end:
                    process.kill()
                    process.wait()
                    raise ValueError('Word не завершил преобразование. Проверьте открытые окна Word и повторите сборку.')
                # Keep painting the progress window during Word's synchronous COM export.
                from PySide6.QtCore import QCoreApplication, QEventLoop
                QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                time.sleep(.04)
        if process.returncode:
            detail = (folder / 'output.log').read_bytes().decode('utf-8', errors='replace')[-1800:]
            log_root = Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir()) / 'StroyID' / 'logs'
            log_root.mkdir(parents=True, exist_ok=True)
            log_path = log_root / ('word-' + str(time.time_ns()) + '.txt')
            log_path.write_text(detail, encoding='utf-8')
            raise ValueError('Word не завершил преобразование документа. Исходники сохранены.\nЖурнал: ' + str(log_path) + '\n' + detail)
    for _, target in jobs:
        if not Path(target).is_file() or not Path(target).stat().st_size:
            raise ValueError('Word не создал PDF документа')


from document_tags import schema
SIGNER_ROLES = schema()['roles']


def sample_docx(section, title, target):
    """A real editable example showing supported tags and repeating table rows."""
    if section == 'quantity':
        Path(target).write_bytes((Path(__file__).parent / 'ui/reference-templates/quantities.docx').read_bytes())
        return Path(target)
    ET.register_namespace('w', W)
    document = ET.Element('{' + W + '}document')
    body = ET.SubElement(document, '{' + W + '}body')
    def paragraph(parent, text, bold=False, center=False):
        p = ET.SubElement(parent, '{' + W + '}p')
        if center:
            prop = ET.SubElement(p, '{' + W + '}pPr')
            ET.SubElement(prop, '{' + W + '}jc', {'{' + W + '}val': 'center'})
        run = ET.SubElement(p, '{' + W + '}r')
        if bold:
            prop = ET.SubElement(run, '{' + W + '}rPr')
            ET.SubElement(prop, '{' + W + '}b')
        ET.SubElement(run, '{' + W + '}t', {XML_SPACE: 'preserve'}).text = text
    def table(headers, tags):
        tbl = ET.SubElement(body, '{' + W + '}tbl')
        prop = ET.SubElement(tbl, '{' + W + '}tblPr')
        ET.SubElement(prop, '{' + W + '}tblW', {'{' + W + '}w': '0', '{' + W + '}type': 'auto'})
        borders = ET.SubElement(prop, '{' + W + '}tblBorders')
        for side in ('top', 'bottom', 'left', 'right', 'insideH', 'insideV'):
            ET.SubElement(borders, '{' + W + '}' + side, {'{' + W + '}val': 'single', '{' + W + '}sz': '4'})
        for i, texts in enumerate((headers, tags)):
            row = ET.SubElement(tbl, '{' + W + '}tr')
            row_props = ET.SubElement(row, '{' + W + '}trPr')
            ET.SubElement(row_props, '{' + W + '}cantSplit')
            if not i:
                ET.SubElement(row_props, '{' + W + '}tblHeader')
            for text in texts:
                cell = ET.SubElement(row, '{' + W + '}tc')
                widths = (500, 5600, 3300) if section == 'photos' else (500, 5700, 1900, 1300) if section == 'reg' else (500, 1200, 4500, 1800, 1400)
                cell_index = len(list(row.findall('{' + W + '}tc'))) - 1
                prop = ET.SubElement(cell, '{' + W + '}tcPr')
                ET.SubElement(prop, '{' + W + '}tcW', {'{' + W + '}w': str(widths[cell_index]), '{' + W + '}type': 'dxa'})
                paragraph(cell, text, bold=not i)
    paragraph(body, title.upper(), bold=True, center=True)
    paragraph(body, 'Объект: {{Объект.Наименование}}')
    paragraph(body, 'Адрес: {{Объект.Адрес}}')
    if section == 'title':
        for text in ('{{Участники.Застройщик.Наименование}}', '{{Участники.Техзаказчик.Наименование}}', 'ИСПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ',
                     '{{Комплект.Наименование}}', 'Шифр проекта: {{Объект.Шифр}}', '{{Участники.Генподрядчик.Наименование}}', '{{Комплект.Год}}'):
            paragraph(body, text, center=True)
    elif section == 'reg':
        paragraph(body, '{{Комплект.Наименование}}', center=True)
        table(['№', 'Тип / наименование документа', 'Номер и дата', 'Листы PDF'],
              ['{{Реестр.Номер}}', '{{Реестр.Тип}}: {{Реестр.Наименование}}', '{{Реестр.Номер_Дата}}', '{{Реестр.Листы}}'])
    elif section in ('aosr', 'aook'):
        for text in ('Застройщик / технический заказчик: {{Участники.Застройщик.Наименование}}; {{Участники.Техзаказчик.Наименование}}',
            'Лицо, осуществляющее строительство: {{Участники.Генподрядчик.Наименование}}', 'Проектная организация: {{Участники.Проектировщик.Наименование}}',
            'Акт № {{АОСР.Номер}} от {{АОСР.Дата}}', 'Система: {{Раздел.Наименование}}',
            *['Представитель: {{Подписанты.' + role + '.Описание}}' for role in SIGNER_ROLES],
            '1. Предъявлены работы: {{АОСР.Работы}}', 'Место работ: {{АОСР.МестоРабот}}',
            '2. Рабочая документация: {{АОСР.РабочаяДокументация}}', '3. Применённые материалы: {{АОСР.Материалы}}',
            'Документы качества: {{Документ.ДокументыКачества}}', '4. Подтверждающие документы: {{АОСР.ПодтверждающиеДокументы}}', 'Приложения: {{АОСР.Приложения}}',
            '5. Начало работ: {{АОСР.Начало}}. Окончание: {{АОСР.Окончание}}',
            '6. Нормативные документы: {{АОСР.Нормативы}}', '7. Разрешённые последующие работы: {{АОСР.ПоследующиеРаботы}}',
            *['Подпись __________________ / {{Подписанты.' + role + '.ФамилияИнициалы}} /' for role in SIGNER_ROLES]):
            paragraph(body, text)
    elif section == 'aik':
        for text in ('Акт № {{АИК.Номер}} от {{АИК.Дата}}', 'Система: {{Раздел.Наименование}}', 'Материал: {{АИК.Материал}}',
            'Количество: {{АИК.Количество}}', 'Документы качества: {{Документ.ДокументыКачества}}', 'Примечание: {{Документ.Примечание}}',
            'Заключение комиссии: ___________________________________________', 'Подписи: _____________________________________________________'):
            paragraph(body, text)
    elif section in ('ozhr', 'spj'):
        paragraph(body, '{{Документ.Наименование}}')
        table(['№', 'Дата', 'Работы / место', 'Ответственный', 'Примечание / ссылка'],
              ['{{Строки.Номер}}', '{{Строки.Колонка_1}}', '{{Строки.Колонка_2}}', '{{Строки.Колонка_3}}', '{{Строки.Колонка_4}}'])
    elif section == 'photos':
        paragraph(body, 'К акту № {{АОСР.Номер}} от {{АОСР.Дата}}')
        table(['№', 'Фотография', 'Подпись'], ['{{Фото.Номер}}', '{{Фото.Изображение}}', '{{Фото.Подпись}}'])
    else:
        for text in ('{{Документ.Наименование}}', '№ {{Документ.Номер}} от {{Документ.Дата}}',
            'Система: {{Раздел.Наименование}}', 'Содержание: {{Документ.Содержание}}', 'Примечание: {{Документ.Примечание}}'):
            paragraph(body, text)
    sect = ET.SubElement(body, '{' + W + '}sectPr')
    ET.SubElement(sect, '{' + W + '}pgSz', {'{' + W + '}w': '11906', '{' + W + '}h': '16838'})
    ET.SubElement(sect, '{' + W + '}pgMar', {'{' + W + '}top': '907', '{' + W + '}right': '850', '{' + W + '}bottom': '907', '{' + W + '}left': '1134'})
    content = {
        '[Content_Types].xml': b'''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>''',
        '_rels/.rels': (f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>').encode(),
        'word/_rels/document.xml.rels': (f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{R}/styles" Target="styles.xml"/></Relationships>').encode(),
        'word/document.xml': ET.tostring(document, encoding='utf-8', xml_declaration=True),
        'word/styles.xml': (f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="100"/></w:pPr></w:pPrDefault></w:docDefaults></w:styles>').encode()
    }
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in content.items():
            archive.writestr(name, data)
    return Path(target)
