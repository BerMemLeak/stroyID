"""Physical page geometry, source isolation and real vector frame proof."""
import io, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from pypdf.generic import RectangleObject
from PySide6.QtWidgets import QApplication
from drawing_frame import framed_reader, template_svg, preview, MM
from folder_store import Store
from pdf_export import prepare_export, write_export
APP=QApplication.instance() or QApplication([])

class DrawingFrameTests(unittest.TestCase):
 def source(self):
  writer=PdfWriter();writer.add_blank_page(210*MM,297*MM);writer.add_blank_page(420*MM,297*MM);writer.add_blank_page(297*MM,420*MM).rotate(90)
  p=writer.add_blank_page(500*MM,400*MM);p.cropbox=RectangleObject([10*MM,20*MM,430*MM,317*MM])
  buf=io.BytesIO();writer.write(buf);writer.close();return buf.getvalue()
 def test_mixed_rotation_crop_and_source_unchanged(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'db');data=self.source();reader=PdfReader(io.BytesIO(data));config={'values':{'Объект':'Жилой дом','Шифр':'ВК-001','АОСР':'АОСР-014','Выполнение':'Выполнение 2'}}
   result=framed_reader(reader,[0,1,2,3],config,store)
   for page,(w,h) in zip(result.pages,[(210,297),(420,297),(420,297),(420,297)]):
    self.assertAlmostEqual(float(page.mediabox.width)/MM,w,places=3);self.assertAlmostEqual(float(page.mediabox.height)/MM,h,places=3);self.assertEqual(page.rotation,0)
    text=''.join(page.extract_text().split());self.assertIn('АОСР-014',text);self.assertIn('ВК-001',text);self.assertIn('Жилойдом',text)
   self.assertEqual(reader.pages[2].rotation,90);self.assertAlmostEqual(float(reader.pages[3].cropbox.left),10*MM,places=6)
 def test_real_preview_and_export_preserve_sizes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=Store(root/'db');source=root/'original.pdf';source.write_bytes(self.source());asset=store.import_file(source);config={'values':{'Объект':'Тест','Шифр':'ОВ','АОСР':'АОСР-1'}}
   r=preview(store,{'key':asset['id'],'page':3,'frame':config});self.assertAlmostEqual(r['width'],420,places=1);self.assertTrue(r['image'].startswith('data:image/png;base64,'))
   plan={'object':'Тест','volumes':[{'title':'Выполнение 2','documents':[{'id':'reg','kind':'registry','name':'Реестр'},{'id':'drawing','kind':'pdf','key':asset['id'],'name':'Схема','frame':config}]}]}
   prepared=prepare_export(store,plan);target=root/'combined.pdf';write_export(prepared,target,store);reader=PdfReader(target)
   self.assertEqual(len(reader.pages),5);self.assertAlmostEqual(float(reader.pages[3].mediabox.width)/MM,420,places=3);self.assertEqual(store.asset_path(asset['id'])[0].read_bytes(),self.source())
 def test_bad_custom_template_rejected(self):
  with self.assertRaises(ValueError):template_svg('<svg><script>alert(1)</script></svg>',{})
  with self.assertRaises(ValueError):template_svg('<svg><text>{{Неизвестный}}</text></svg>',{})
  with self.assertRaises(ValueError):template_svg('<svg><image href="file:///secret"/></svg>',{})

 def test_repeated_preview_never_opens_a_temporary_pdf(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=Store(root/'db');source=root/'original.pdf';source.write_bytes(self.source());asset=store.import_file(source)
   # A real QtPdf preview must succeed even when creating temporary files is
   # forbidden. This covers the Windows handle failure without skipping tests.
   with patch('drawing_frame.tempfile.TemporaryDirectory',side_effect=AssertionError('Preview attempted a temporary file')):
    for page in (1,3,2,1):
     result=preview(store,{'key':asset['id'],'page':page})
     self.assertTrue(result['image'].startswith('data:image/png;base64,'))
     self.assertEqual(result['width'],210 if page==1 else 420)
   self.assertEqual(store.asset_path(asset['id'])[0].read_bytes(),self.source())

if __name__=='__main__':unittest.main()
