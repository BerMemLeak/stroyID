"""DOCX content, split-run replacements, repeating rows and PDF source integration."""
import copy
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch
from word_templates import W, TAG, fill_docx, inspect_docx, package, sample_docx, convert_docx_batch
from pdf_export import prepare_export, render_html
from storage import Store
from PySide6.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])


class WordTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def sample(self, kind='title'):
        path = self.root / (kind + '.docx')
        sample_docx(kind, 'Образец ' + kind, path)
        return path

    def context(self, source):
        return {x: 'Значение ' + x for x in inspect_docx(source.read_bytes())['tags'] if '.' not in x}

    def test_split_runs_headers_styles_and_source_unchanged(self):
        original = self.sample()
        parts = package(original.read_bytes())
        root = ET.fromstring(parts['word/document.xml'])
        first = root.find('.//{' + W + '}p')
        for child in list(first):
            first.remove(child)
        for text in ('До {{Об', 'ъект}} после {{Адрес_', 'Объекта}}. {{Объект}}'):
            run = ET.SubElement(first, '{' + W + '}r')
            ET.SubElement(ET.SubElement(run, '{' + W + '}rPr'), '{' + W + '}b')
            ET.SubElement(run, '{' + W + '}t').text = text
        parts['word/document.xml'] = ET.tostring(root)
        parts['word/header1.xml'] = (f'<w:hdr xmlns:w="{W}"><w:p><w:r><w:t>{{{{Объект}}}}</w:t></w:r></w:p></w:hdr>').encode()
        with zipfile.ZipFile(original, 'w') as z:
            for name, body in parts.items():
                z.writestr(name, body)
        before = original.read_bytes()
        values = self.context(original)
        values.update(Объект='Дом & «Боец»', Адрес_Объекта='Москва\nПодъезд 1')
        out = fill_docx(before, self.root / 'filled.docx', values)
        new = package(out.read_bytes())
        text = ''.join(ET.fromstring(new['word/document.xml']).itertext())
        self.assertIn('До Дом & «Боец» после Москва', text)
        self.assertIn('Подъезд 1. Дом & «Боец»', text)
        self.assertIn('Дом & «Боец»', ''.join(ET.fromstring(new['word/header1.xml']).itertext()))
        self.assertEqual(new['word/styles.xml'], parts['word/styles.xml'])
        self.assertTrue(ET.fromstring(new['word/document.xml']).findall('.//{' + W + '}br'))
        self.assertEqual(original.read_bytes(), before)
        self.assertEqual(inspect_docx(out.read_bytes())['tags'], [])

    def test_unused_word_namespaces_remain_declared(self):
        source = self.sample()
        parts = package(source.read_bytes())
        data = parts['word/document.xml'].decode()
        data = data.replace('<w:document ', '<w:document xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14" ', 1)
        parts['word/document.xml'] = data.encode()
        with zipfile.ZipFile(source, 'w') as z:
            for name, body in parts.items():
                z.writestr(name, body)
        out = fill_docx(source.read_bytes(), self.root / 'namespaces.docx', self.context(source))
        data = package(out.read_bytes())['word/document.xml']
        self.assertIn(b'xmlns:w14=', data)
        self.assertIn(b'Ignorable="w14"', data)
        ET.fromstring(data)

    def test_registry_repeated_rows_and_empty_list(self):
        source = self.sample('reg')
        values = self.context(source)
        rows = [{'Номер': i + 1, 'Тип': 'АОСР', 'Наименование': 'Монтаж ' + str(i),
                 'Номер_Дата': '№ А-' + str(i), 'Листы': str(i + 4)} for i in range(4)]
        out = fill_docx(source.read_bytes(), self.root / 'rows.docx', values, {'Реестр': rows})
        doc = ET.fromstring(package(out.read_bytes())['word/document.xml'])
        self.assertEqual(len(doc.findall('.//{' + W + '}tr')), 5)
        self.assertIn('Монтаж 3', ''.join(doc.itertext()))
        out = fill_docx(source.read_bytes(), self.root / 'empty.docx', values, {'Реестр': []})
        self.assertEqual(len(ET.fromstring(package(out.read_bytes())['word/document.xml']).findall('.//{' + W + '}tr')), 1)

    def test_unknown_tags_are_blocking(self):
        source = self.sample()
        with self.assertRaisesRegex(ValueError, 'Неизвестные теги'):
            fill_docx(source.read_bytes(), self.root / 'missing.docx', {})
        self.assertFalse((self.root / 'missing.docx').exists())

    def test_photos_insert_real_image_relationship(self):
        import base64
        from PySide6.QtCore import QBuffer, QIODevice
        from PySide6.QtGui import QImage
        img = QImage(120, 60, QImage.Format.Format_RGB32)
        img.fill(0xff555555)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buffer, 'PNG')
        source = self.sample('photos')
        photo = 'data:image/png;base64,' + base64.b64encode(bytes(buffer.data())).decode()
        out = fill_docx(source.read_bytes(), self.root / 'photos-filled.docx', self.context(source),
                        {'Фото': [{'Номер': 1, 'Подпись': 'Монтаж', 'Изображение': photo}]})
        parts = package(out.read_bytes())
        self.assertEqual(len([x for x in parts if x.startswith('word/media/')]), 1)
        self.assertIn(b'wordprocessingDrawing', parts['word/document.xml'])
        self.assertEqual(inspect_docx(out.read_bytes())['tags'], [])
        with self.assertRaisesRegex(ValueError, 'Фото не загружено'):
            fill_docx(source.read_bytes(), self.root / 'bad-photo.docx', self.context(source),
                        {'Фото': [{'Номер': 1, 'Подпись': '', 'Изображение': ''}]})

    def test_word_pdf_counts_and_registry_use_filled_docx(self):
        title, reg = self.sample(), self.sample('reg')
        store = Store(self.root / 'db')
        a, b = store.import_file(title), store.import_file(reg)
        seen = []
        def converter(jobs):
            for source, target in jobs:
                text = ''.join(ET.fromstring(package(Path(source).read_bytes())['word/document.xml']).itertext())
                self.assertNotIn('{{', text)
                seen.append(text)
                render_html('<h2>' + ('Реестр' if 'Монтаж' in text else 'Word-титул') + '</h2><p>' + text + '</p>', target)
        plan = {'object': 'Дом', 'volumes': [{'title': 'Том 1', 'documents': [
            {'id': 'title', 'kind': 'word', 'name': 'Титул', 'templateKey': a['id'], 'values': self.context(title)},
            {'id': 'reg', 'kind': 'registry', 'name': 'Реестр', 'templateKey': b['id'], 'values': self.context(reg)},
            {'id': 'act', 'kind': 'html', 'name': 'Монтаж', 'type': 'АОСР', 'html': '<h2>Монтаж</h2>'}]}]}
        try:
            with patch('pdf_export.convert_docx_batch', converter):
                prepared = prepare_export(store, plan)
            self.assertEqual(prepared['pages'], 3)
            self.assertEqual(prepared['volumes'][0]['documents'][2]['start'], 3)
            self.assertTrue(any('Монтаж' in text and '3' in text for text in seen))
            with patch('pdf_export.convert_docx_batch', side_effect=ValueError('Word не установлен')):
                with self.assertRaisesRegex(ValueError, 'Word не установлен'):
                    prepare_export(store, plan)
            self.assertEqual(title.read_bytes(), store.asset_path(a['id'])[0].read_bytes())
        finally:
            store.close()

    def test_missing_pdf_preflight_does_not_start_word(self):
        source = self.sample()
        store = Store(self.root / 'db')
        asset = store.import_file(source)
        plan = {'volumes': [{'documents': [
            {'name': 'Титул', 'kind': 'word', 'templateKey': asset['id'], 'values': self.context(source)},
            {'name': 'Протокол', 'kind': 'pdf', 'key': ''}]}]}
        try:
            with patch('pdf_export.convert_docx_batch') as converter:
                with self.assertRaisesRegex(ValueError, 'Протокол'):
                    prepare_export(store, plan)
                converter.assert_not_called()
        finally:
            store.close()
