"""Quantities repeat as editable rows; act sheet references use actual output counts."""
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from pypdf import PdfWriter
from storage import Store
from word_templates import fill_docx, inspect_docx, package
from pdf_export import prepare_export
from pdf_text import page_text

class QuantitiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_collection_repeats_and_original_is_unchanged(self):
        source = Path(__file__).resolve().parents[1] / 'ui/reference-templates/quantities.docx'
        data = source.read_bytes()
        values = {k: '' for k in inspect_docx(data)['tags'] if '.' not in k}
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / 'filled.docx'
            fill_docx(data, target, values, {'Объемы': [
                {'Номер': '1', 'Наименование': 'Труба', 'Место': 'Этаж 1', 'Единица': 'м', 'Количество': '12,5'},
                {'Номер': '2', 'Наименование': 'Хомут', 'Место': 'Этаж 2', 'Единица': 'шт.', 'Количество': '20'}]})
            text = package(target.read_bytes())['word/document.xml'].decode()
            for word in ('Труба', 'Хомут', '12,5', '20'):
                self.assertIn(word, text)
            self.assertFalse(inspect_docx(target.read_bytes())['tags'])
            fill_docx(data, target, values, {'Объемы': []})
            self.assertFalse(inspect_docx(target.read_bytes())['tags'])
        self.assertEqual(data, source.read_bytes())

    def test_actual_three_page_attachment_updates_act_and_registry(self):
        marker = '[[QUANTITY_SHEETS:one]]'
        with tempfile.TemporaryDirectory() as root:
            store = Store(Path(root) / 'data')
            def convert(jobs):
                for _, target in jobs:
                    writer = PdfWriter()
                    for _ in range(3):writer.add_blank_page(595, 842)
                    writer.write(target);writer.close()
            template = Path(__file__).resolve().parents[1] / 'ui/reference-templates/quantities.docx'
            values = {k: '' for k in inspect_docx(template.read_bytes())['tags'] if '.' not in k}
            act = {'id':'act', 'kind':'html', 'html':'<p>Ведомость: '+marker+' л.</p>',
                   'attachmentPageRefs':{marker:'quantity:one'}}
            plan = {'volumes':[{'documents':[{'kind':'registry'},act,
                {'id':'quantity:one','kind':'word','builtinTemplate':'quantity','values':values,'collections':{'Объемы':[]}}]}]}
            try:
                with patch('pdf_export.convert_docx_batch',side_effect=convert):
                    result=prepare_export(store,plan)
                docs=result['volumes'][0]['documents']
                self.assertEqual(docs[2]['count'],3)
                self.assertIn('3 л.',page_text(docs[1]['reader'].pages[0]))
                self.assertNotIn(marker,docs[1]['html'])
                self.assertIn(marker,act['html'])
                self.assertEqual(docs[2]['start'],3)
                self.assertEqual(docs[2]['end'],5)
                self.assertIn('3-5',page_text(docs[0]['reader'].pages[0]))
            finally:store.close()
