import io
import os
import tempfile
import unittest
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen') if os.name != 'nt' else None
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter
from storage import Store
from pdf_export import prepare_export, render_html, write_export
from pdf_text import page_text


class PdfExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        source = PdfWriter()
        for i in range(3):
            data = render_html('<h2>Исходный лист ' + str(i + 1) + '</h2>', self.root / f'{i}.pdf')
            source.append(PdfReader(io.BytesIO(data)), import_outline=False)
        # A drawing may have a different format and rotation; it must remain intact.
        source.pages[1].rotate(90)
        source.pages[1].mediabox.upper_right = (841, 595)
        with (self.root / 'source.pdf').open('wb') as stream:
            source.write(stream)
        source.close()
        self.asset = self.store.import_file(self.root / 'source.pdf')

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_order_actual_pages_ranges_bookmarks_and_source_unchanged(self):
        original = self.store.asset_path(self.asset['id'])[0].read_bytes()
        plan = {'object': 'Проверочный объект', 'volumes': [
            {'title': 'Том системы', 'documents': [
                {'kind': 'html', 'name': 'Титульный лист', 'html': '<h2>Том системы</h2>'},
                {'kind': 'registry', 'name': 'Реестр'},
                {'kind': 'pdf', 'name': 'Выбранные листы', 'key': self.asset['id'], 'from': 2, 'to': 3, 'pages': 99}]},
            {'title': 'Другой том', 'documents': [
                {'kind': 'html', 'name': 'Титул второго тома', 'html': '<h2>Другой том</h2>'},
                {'kind': 'registry', 'name': 'Реестр второго тома'},
                {'kind': 'pdf', 'name': 'Полный исходник', 'key': self.asset['id'], 'pages': 1}]}]}
        prepared = prepare_export(self.store, plan)
        result = write_export(prepared, self.root / 'result.pdf', self.store)
        reader = PdfReader(result['path'])
        self.assertEqual(result['pages'], 9)
        self.assertEqual(len(reader.pages), 9)
        self.assertIn('Исходный лист 2', page_text(reader.pages[2]))
        self.assertIn('Исходный лист 3', page_text(reader.pages[3]))
        self.assertEqual(reader.pages[2].rotation, 90)
        self.assertEqual(tuple(reader.pages[2].mediabox), (0, 0, 841, 595))
        self.assertEqual(prepared['volumes'][0]['documents'][2]['start'], 3)
        self.assertEqual(prepared['volumes'][1]['documents'][2]['start'], 7)
        self.assertIn('3-4', reader.pages[1].extract_text())
        self.assertIn('7-9', reader.pages[5].extract_text())
        self.assertEqual(len(reader.outline), 4)  # two volume nodes with children
        self.assertEqual(self.store.asset_path(self.asset['id'])[0].read_bytes(), original)

    def test_missing_sources_and_bad_ranges_are_not_silently_skipped(self):
        target = self.root / 'result.pdf'
        target.write_bytes(b'keep previous output')
        plan = {'volumes': [{'title': 'Том', 'documents': [
            {'kind': 'pdf', 'name': 'Паспорт без файла', 'key': ''},
            {'kind': 'pdf', 'name': 'Схема с неверными листами', 'key': self.asset['id'], 'from': 2, 'to': 8}]}]}
        with self.assertRaises(ValueError) as error:
            prepare_export(self.store, plan)
        self.assertIn('Паспорт без файла', str(error.exception))
        self.assertIn('Схема с неверными листами', str(error.exception))
        self.assertEqual(target.read_bytes(), b'keep previous output')

    def test_encrypted_and_corrupt_sources_rejected(self):
        encrypted = PdfWriter()
        encrypted.add_blank_page(width=100, height=100)
        encrypted.encrypt('secret')
        encrypted.write(self.root / 'encrypted.pdf')
        (self.root / 'broken.pdf').write_bytes(b'not a pdf')
        for name in ['encrypted.pdf', 'broken.pdf']:
            key = self.store.import_file(self.root / name)['id']
            with self.assertRaises(ValueError):
                prepare_export(self.store, {'volumes': [{'title': 'Том', 'documents': [
                    {'kind': 'pdf', 'name': name, 'key': key}]}]})

    def test_long_registry_converges_and_global_ranges_match(self):
        docs = [{'kind': 'html', 'name': 'Титульный', 'html': '<h2>Титульный лист</h2>'},
                {'kind': 'registry', 'name': 'Реестр'}]
        docs.extend({'kind': 'pdf', 'key': self.asset['id'], 'from': 1, 'to': 1,
                     'name': 'Документ с длинным названием ' + str(i), 'nd': '№ ' + str(i)} for i in range(65))
        prepared = prepare_export(self.store, {'volumes': [{'title': 'Большой том', 'documents': docs}]})
        registry = prepared['volumes'][0]['documents'][1]
        self.assertGreater(registry['count'], 1)
        self.assertEqual(prepared['pages'], 66 + registry['count'])
        self.assertEqual(prepared['volumes'][0]['documents'][-1]['end'], prepared['pages'])
        result = write_export(prepared, self.root / 'long.pdf', self.store)
        self.assertEqual(len(PdfReader(result['path']).pages), prepared['pages'])

    def test_export_cannot_overwrite_managed_original(self):
        prepared = prepare_export(self.store, {'volumes': [{'documents': [
            {'kind': 'pdf', 'name': 'Исходник', 'key': self.asset['id']}]}]})
        with self.assertRaises(ValueError):
            write_export(prepared, self.store.asset_path(self.asset['id'])[0], self.store)


if __name__ == '__main__':
    unittest.main()
