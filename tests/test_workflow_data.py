"""Shared certificate storage and image tags must survive real file round trips."""
import base64, io, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer, QIODevice
from pypdf import PdfWriter
from folder_store import Store
from test_workspace_v8 import state, project
from word_templates import fill_docx, inspect_docx, package, WORD_SCRIPT
from drawing_frame import resolve_frame_font
APP=QApplication.instance() or QApplication([])
ROOT=Path(__file__).resolve().parents[1]
class WorkflowDataTests(unittest.TestCase):
 def test_shared_quality_roundtrip_portable_and_independent_edits(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=Store(root/'base');s=state();p=project();s['projects']=[p]
   w=PdfWriter();w.add_blank_page(595,842);w.write(root/'source.pdf');asset=store.import_file(root/'source.pdf')
   s['lib']['quality']=[{'id':'q1','type':'Сертификат','num':'77','validFrom':'2026-01-01','validTo':'2027-01-01','date':'2026-01-01','file':asset['name'],'fileKey':asset['id'],'pages':1}]
   p['materials']=[{'id':'m1','name':'Труба 20','docs':[],'docIds':['q1']},{'id':'m2','name':'Труба 40','docs':[],'docIds':['q1']}]
   result=store.save(s,0);loaded=result['state'];doc=loaded['lib']['quality'][0]
   self.assertTrue(doc['fileKey'].startswith('Справочники/Документы качества/'))
   self.assertEqual(len([f for f in (store.root/'Справочники').rglob('*.pdf') if 'История версий' not in f.parts]),1)
   self.assertEqual(len([f for f in (store.root/'Справочники').rglob('*.pdf') if 'История версий' in f.parts]),1)
   self.assertFalse(list((store.root/p['short']).rglob('*.pdf')))
   loaded['projects'][0]['materials'][0]['docIds']=[];doc['num']='78';result=store.save(loaded,result['revision'])
   self.assertEqual(result['state']['projects'][0]['materials'][1]['docIds'],['q1'])
   target=root/'portable.zip';store.portable_export(result['state'],target)
   with zipfile.ZipFile(target) as z:z.extractall(root/'other')
   other=Store(root/'other/СтройИД');r=other.load();self.assertEqual(r['state']['lib']['quality'][0]['num'],'78');self.assertFalse(r['warnings']);self.assertTrue(other.asset_path(r['state']['lib']['quality'][0]['fileKey'])[0].is_file());other.close();store.close()
 def test_user_title_logo_is_an_image_not_base64_text(self):
  source=ROOT/'ui/reference-templates/title.docx';image=QImage(300,80,QImage.Format.Format_RGB32);image.fill(0xff224466);buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
  values={tag:'Проверка' for tag in inspect_docx(source.read_bytes())['tags']};values['Логотип_Компании']='data:image/png;base64,'+base64.b64encode(bytes(buffer.data())).decode()
  with tempfile.TemporaryDirectory() as tmp:
   out=fill_docx(source.read_bytes(),Path(tmp)/'title.docx',values);parts=package(out.read_bytes())
   self.assertIn(b'wordprocessingDrawing',parts['word/document.xml']);self.assertNotIn(b'data:image',parts['word/document.xml']);self.assertEqual(len([k for k in parts if k.startswith('word/media/stroiid-')]),1);self.assertEqual(inspect_docx(out.read_bytes())['tags'],[])
 def test_missing_production_font_is_explicit(self):
  with patch('drawing_frame.QFontDatabase.families',return_value=['Arial']):
   with self.assertRaisesRegex(ValueError,'ISOCPEUR'):resolve_frame_font({'requireFont':True})
 def test_windows_jobs_parse_single_root_array(self):
  self.assertIn("$jobs=ConvertFrom-Json -InputObject",WORD_SCRIPT)
  self.assertIn("$job.source -isnot [string]",WORD_SCRIPT)
if __name__=='__main__':unittest.main()
