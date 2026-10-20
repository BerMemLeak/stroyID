"""Physical page geometry, source isolation and real vector frame proof."""
import io, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from pypdf.generic import RectangleObject
from PySide6.QtWidgets import QApplication
from drawing_frame import framed_reader, template_svg, preview, frame_signer_values, MM
from folder_store import Store
from pdf_export import prepare_export, write_export
APP=QApplication.instance() or QApplication([])

class DrawingFrameTests(unittest.TestCase):
 def test_ordered_signer_slots_and_empty_unused_cells(self):
  rows=[{'role':'Разработал','name':'Морозкин Е. Е.'}, {'role':'Проверил','name':'Щербак О. О.'}]
  values=frame_signer_values({'signerRows':rows},{'Дата':'20.05.2025'})
  self.assertEqual(values['Роль_1'],'Разработал');self.assertEqual(values['Подписант_2'],'Щербак О. О.')
  self.assertEqual(values['Дата_Подписанта_1'],'20.05.2025')
  for i in range(3,7):
   for key in ('Роль','Подписант','Дата_Подписанта'):self.assertEqual(values[f'{key}_{i}'],'')
  blank=frame_signer_values({'signerRows':[]},{'Разработал':'Старое имя','Дата':'20.05.2025'})
  self.assertEqual(blank['Подписант_1'],'');self.assertEqual(blank['Дата_Подписанта_1'],'')

 def test_signer_limit_rejects_overflow_and_malformed_rows(self):
  for rows in ([{}]*7,{},[None],[{'role':7}],[{'name':[]} ]):
   with self.assertRaises(ValueError):frame_signer_values({'signerRows':rows},{})
  self.assertEqual(frame_signer_values({'signerRows':[{}]*6},{})['Роль_6'],'')

 def test_all_six_signer_rows_in_real_pdf_preserve_order_and_duplicate_roles(self):
  with tempfile.TemporaryDirectory() as tmp:
   rows=[{'role':role,'name':'Участник '+str(i+1)} for i,role in enumerate(
    ['Разработал','Рук. проекта','Производ. работ','Строит. контр.','Строит. контр.','Утвердил'])]
   result=framed_reader(PdfReader(io.BytesIO(self.source())),[1],
    {'signerRows':rows,'values':{'Дата':'20.05.2025'}},Store(Path(tmp)/'db'))
   text=''.join(result.pages[0].extract_text().split())
   for i in range(6):self.assertIn('Участник'+str(i+1),text)
   self.assertEqual(text.count('Строит.контр.'),2)
   self.assertEqual(text.count('20.05.2025'),6)
   self.assertLess(text.index('Участник1'),text.index('Участник6'))

 def test_legacy_signers_keep_original_cells(self):
  values=frame_signer_values({}, {'Разработал':'Первый','Проверил':'Второй','Нормоконтроль':'Пятый'})
  self.assertEqual(values['Подписант_1'],'Первый');self.assertEqual(values['Подписант_2'],'Второй')
  self.assertEqual(values['Роль_3'],'');self.assertEqual(values['Подписант_5'],'Пятый')

 def test_custom_template_must_support_configured_row_slots(self):
  from drawing_frame import frame_page
  writer=PdfWriter();page=writer.add_blank_page(420*MM,297*MM)
  with self.assertRaisesRegex(ValueError,'не поддерживает выбранные строки'):
   frame_page(page,{'signerRows':[{'role':'Разработал','name':'Иванов'}]},
    template='<svg xmlns="http://www.w3.org/2000/svg"><text>{{Разработал}}</text></svg>')

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
 def test_every_page_has_total_attachment_and_original_source_scale(self):
  from PySide6.QtGui import QPainter, QPdfWriter
  from PySide6.QtCore import QMarginsF
  from PySide6.QtGui import QPageSize
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);src=root/'edge.pdf';writer=QPdfWriter(str(src))
   writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3));writer.setPageMargins(QMarginsF(0,0,0,0));writer.setResolution(72)
   painter=QPainter(writer)
   for i in range(3):
    if i:writer.newPage()
    painter.drawText(5,15,'SOURCE-TOP');painter.drawText(5,writer.height()-5,'SOURCE-BOTTOM')
   painter.end();del painter,writer
   reader=PdfReader(src);store=Store(root/'db')
   cfg={'fitContent':True,'values':{'АОСР':'ACT-42','Номер_Приложения':'2','Дата_Акта':'18.10.2026','Стадия':'ИД'}}
   result=framed_reader(reader,[0,1,2],cfg,store)
   for i,page in enumerate(result.pages):
    text=''.join(page.extract_text().split());self.assertIn('ACT-42',text);self.assertIn('18.10.2026',text)
    found=[]
    page.extract_text(visitor_text=lambda text,cm,tm,*args:found.append((text,cm,tm)))
    original=[]
    reader.pages[i].extract_text(visitor_text=lambda text,cm,tm,*args:original.append((text,cm,tm)))
    before=[(t,cm,tm) for t,cm,tm in original if 'SOURCE' in t]
    after=[(t,cm,tm) for t,cm,tm in found if 'SOURCE' in t]
    self.assertEqual(before,after)  # Legacy fitContent must never scale or move content.
    # Total and sheet are separate text spans at the title block positions.
    self.assertTrue(any(text.strip()=='3' for text,_,_ in found))
    self.assertTrue(any(text.strip()==str(i+1) for text,_,_ in found))
   selected=framed_reader(reader,[1],cfg,store)
   text=''.join(selected.pages[0].extract_text().split());self.assertIn('ACT-42',text)
   self.assertIn('3',text)  # Total is source PDF size even when exporting a range.
   self.assertNotIn('ACT-42',reader.pages[0].extract_text())

 def test_long_title_is_separate_readable_lines(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'db');reader=PdfReader(io.BytesIO(self.source()))
   title='Исполнительная схема устройства системы водоснабжения первого этажа в осях 1–7 / Д–Ж'
   result=framed_reader(reader,[1],{'values':{'Название_Схемы':title}},store)
   spans=[]
   def visit(text,cm,tm,font,size):
    normalized=''.join(text.split())
    if normalized and any(word in normalized for word in ('Исполнительная','водоснабжения','осях')):
     y=tm[4]*cm[1]+tm[5]*cm[3]+cm[5]
     effective=size*(cm[2]**2+cm[3]**2)**0.5
     spans.append((normalized,y,effective))
   result.pages[0].extract_text(visitor_text=visit)
   self.assertGreaterEqual(len(spans),2)
   self.assertGreater(len({round(y,1) for _,y,_ in spans}),1)
   self.assertTrue(all(size>=3.4*MM for _,_,size in spans),spans)
   self.assertTrue(all(5*MM<y<20*MM for _,y,_ in spans),spans)

 def test_section_attachment_on_every_selected_sheet(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'db');reader=PdfReader(io.BytesIO(self.source()))
   cfg={'values':{'Основание_Приложения':'К разделу','Шифр_Приложения':'SECTION-042',
      'Номер_Приложения':'7','Дата_Приложения':'"15" 09.2026г.'}}
   result=framed_reader(reader,[0,1,2],cfg,store)
   for page in result.pages:
    text=''.join(page.extract_text().split())
    self.assertIn('Кразделу',text);self.assertIn('SECTION-042',text)
    self.assertIn('"15"09.2026г.',text);self.assertIn('Приложение№',text)
   self.assertNotIn('SECTION-042',reader.pages[0].extract_text())

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
