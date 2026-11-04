import copy
import io
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter
from storage import Store
from test_storage import state
from material_import import preview_import, commit_import
from pdf_export import prepare_export
from act_registers import expand_registers, ActPageError
from print_export import write_print_folder

ROOT=Path(__file__).resolve().parents[1]


def fixture_xlsx(path, rows):
    """Patch data cells in the actual distributed template; don't build a second schema."""
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(ROOT/'ui/reference-templates/materials-import.xlsx') as z:
        parts={n:z.read(n) for n in z.namelist()}
    root=ET.fromstring(parts['xl/worksheets/sheet1.xml']);data=root.find('{'+ns+'}sheetData')
    for row in list(data)[1:]:data.remove(row)
    for ri, cells in enumerate(rows,2):
        row=ET.SubElement(data,'{'+ns+'}row',r=str(ri))
        for ci,value in enumerate(cells):
            if value is None:continue
            n=ci+1;col=''
            while n:n,a=divmod(n-1,26);col=chr(65+a)+col
            cell=ET.SubElement(row,'{'+ns+'}c',r=col+str(ri),t='inlineStr')
            ET.SubElement(ET.SubElement(cell,'{'+ns+'}is'),'{'+ns+'}t').text=str(value)
    parts['xl/worksheets/sheet1.xml']=ET.tostring(root)
    with zipfile.ZipFile(path,'w') as z:
        for name,value in parts.items():z.writestr(name,value)


def pdf(path, sizes):
    writer=PdfWriter()
    for w,h in sizes:writer.add_blank_page(w,h)
    writer.write(path);writer.close()


class PrintMaterialsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=Store(self.root/'db');self.s=self.store.save(state(),0)['state']
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def preview(self,rows):
        x=self.root/'input.xlsx';fixture_xlsx(x,rows)
        preview=preview_import(x,self.root,self.s);preview['heads']=copy.deepcopy(self.store.heads)
        return preview
    def test_one_row_two_documents_roundtrip_and_duplicate_skip(self):
        pdf(self.root/'passport.pdf',[(595,842)]);pdf(self.root/'certificate.pdf',[(842,1191)])
        rows=[['M001','Кирпич','М150','Паспорт качества','','','passport.pdf','Сертификат соответствия','123','01.10.2025','certificate.pdf']]
        preview=self.preview(rows);self.assertFalse(preview['errors']);self.assertEqual(len(preview['items']),1)
        result=commit_import(self.store,preview,{'2':'new'})
        self.assertFalse(result['warnings']);self.assertFalse(result['conflicts'])
        material=result['state']['lib']['base'][0];self.assertEqual(len(material['docs']),2)
        (self.root/'passport.pdf').unlink()
        self.assertTrue(self.store.asset_path(material['docs'][0]['fileKey'])[0].is_file())
        # Repeat with the same source bytes and select the existing material.
        src=self.store.asset_path(material['docs'][0]['fileKey'])[0];(self.root/'passport.pdf').write_bytes(src.read_bytes())
        self.s=result['state'];again=self.preview(rows)
        result=commit_import(self.store,again,{'2':material['id']})
        self.assertEqual(result['importedDocuments'],0);self.assertEqual(result['skippedDocuments'],2)
        self.assertEqual(len(result['state']['lib']['base']),1)
    def test_invalid_source_blocks_every_row_and_path_escape(self):
        pdf(self.root/'valid.pdf',[(595,842)])
        p=self.preview([['M1','Первый','','Паспорт','','','valid.pdf'],['M2','Второй','','Паспорт','','','../outside.pdf']])
        self.assertTrue(p['errors'])
        with self.assertRaises(ValueError):commit_import(self.store,p,{'2':'new','3':'new'})
        self.assertEqual(self.store.load()['state']['lib']['base'],[])
    def test_changed_file_or_card_blocks_commit(self):
        pdf(self.root/'valid.pdf',[(595,842)])
        p=self.preview([['M1','Материал','','Паспорт','','','valid.pdf']])
        pdf(self.root/'valid.pdf',[(595,842),(595,842)])
        with self.assertRaisesRegex(ValueError,'изменился'):commit_import(self.store,p,{'2':'new'})
        self.assertEqual(self.store.load()['state']['lib']['base'],[])
        p=self.preview([['M1','Материал','','Паспорт','','','valid.pdf']])
        changed=self.store.load()['state'];changed['lib']['base'].append({'id':'other','name':'Другой','brand':'','maker':'','category':'','docs':[]})
        self.store.save(changed,self.store.revision)
        with self.assertRaisesRegex(ValueError,'База изменилась'):commit_import(self.store,p,{'2':'new'})
    def test_invalid_date_duplicate_material_and_broken_pdf(self):
        (self.root/'bad.pdf').write_bytes(b'not a PDF')
        p=self.preview([['M1','Материал','','Паспорт','','32.13.2025','bad.pdf'],['M1','Материал','','Сертификат','','','bad.pdf']])
        self.assertGreaterEqual(len(p['errors']),4)
    def test_registers_preserve_source_and_reference_one_another(self):
        item={'id':'a1','kind':'html','type':'АОСР','name':'Работы','html':'<p>Материал</p>',
            'actRegister':{'actId':'1','number':'АР-1','values':{'АОСР.Материалы':'Материал','АОСР.Приложения':'Схема','АОСР.Дата':'01.10.2025'},
                'entries':{'materials':['Материал; марка и сертификат'],'evidence':['Схема'],'attachments':['Схема']},
                'settings':{k:{'enabled':True} for k in ['materials','evidence','attachments']}}}
        original=copy.deepcopy(item);plan={'volumes':[{'title':'Том','documents':[item]}]};expanded=expand_registers(plan)
        self.assertEqual(item,original)
        docs=expanded['volumes'][0]['documents'];self.assertEqual(len(docs),4)
        self.assertIn('АР-1-М',docs[0]['html']);self.assertIn('АР-1-Д',docs[-1]['html'])
        self.assertIn('Материал; марка и сертификат',docs[1]['html'])
    def test_act_overflow_is_blocked_and_one_page_is_padded(self):
        pdf(self.root/'one.pdf',[(595,842)]);a=self.store.import_file(self.root/'one.pdf')
        plan={'volumes':[{'title':'Том','documents':[{'id':'a','kind':'pdf','type':'АОСР','name':'Акт','key':a['id']}]}]}
        ready=prepare_export(self.store,plan);self.assertEqual(ready['pages'],2)
        pdf(self.root/'three.pdf',[(595,842)]*3);a=self.store.import_file(self.root/'three.pdf')
        plan['volumes'][0]['documents'][0]['key']=a['id']
        with self.assertRaises(ActPageError) as err:prepare_export(self.store,plan)
        self.assertEqual(err.exception.details[0]['pages'],3)
    def test_real_pagination_moves_long_list_into_register(self):
        import html
        entries=['Материал номер '+str(i)+' с подробным описанием марки и паспорта качества.' for i in range(160)]
        raw='\n'.join(entries)
        item={'id':'a1','kind':'html','type':'АОСР','name':'Работы',
            'html':'<h2>АОСР</h2><div class="pl" data-act-tag="АОСР.Материалы">'+html.escape(raw).replace('\n','<br>')+'</div><div class="pl" data-act-tag="АОСР.Приложения">&nbsp;</div>',
            'actRegister':{'actId':'1','number':'АР-1','values':{'АОСР.Материалы':raw,'АОСР.Дата':'01.10.2025'},
                'entries':{'materials':entries},'settings':{}}}
        plan={'volumes':[{'title':'Том','documents':[item]}]}
        with self.assertRaises(ActPageError) as error:prepare_export(self.store,plan)
        self.assertIn('materials',error.exception.details[0]['suggested'])
        item['actRegister']['settings']={'materials':{'enabled':True}}
        result=prepare_export(self.store,plan);docs=result['volumes'][0]['documents']
        self.assertEqual(docs[0]['count'],2);self.assertGreater(docs[1]['count'],2)
        self.assertIn('Реестр материалов',' '.join(docs[0]['reader'].pages[0].extract_text().split()))
        self.assertEqual(item['actRegister']['values']['АОСР.Материалы'],raw)
    def test_builtin_register_fills_canonical_template_and_real_attachment_counts(self):
        from word_templates import inspect_docx,package
        template=ROOT/'ui/reference-templates/act-register.docx'
        from document_tags import collection_tags
        values={k:'Тест' for k in inspect_docx(template.read_bytes())['tags'] if k not in collection_tags()}
        values.update({'АОСР.Приложения':'Ведомость [[QUANTITY_SHEETS:q]] л.','АОСР.Дата':'01.10.2025'})
        act={'id':'a','kind':'html','type':'АОСР','name':'Акт','html':'<p>Приложения</p>',
            'attachmentPageRefs':{'[[QUANTITY_SHEETS:q]]':'q'},
            'actRegister':{'actId':'a','number':'АР-1','values':values,'builtinTemplate':'act-register',
                'entries':{'attachments':['Ведомость [[QUANTITY_SHEETS:q]] л.']},'settings':{'attachments':{'enabled':True}}}}
        pdf(self.root/'q.pdf',[(595,842)]*3);source=self.store.import_file(self.root/'q.pdf')
        plan={'volumes':[{'title':'Том','documents':[act,{'id':'q','kind':'pdf','name':'Ведомость','key':source['id']}]}]}
        seen=[]
        def convert(jobs):
            for src,dst in jobs:
                data=Path(src).read_bytes();self.assertFalse(inspect_docx(data)['tags'])
                seen.append(package(data)['word/document.xml'].decode())
                pdf(dst,[(595,842)])
        with patch('pdf_export.convert_docx_batch',convert):result=prepare_export(self.store,plan)
        self.assertEqual(result['documents'],3)
        self.assertNotIn('[[QUANTITY_SHEETS:q]]',seen[-1]);self.assertIn('Ведомость 3 л.',seen[-1])
    def test_print_groups_rotation_blank_backs_and_input_unchanged(self):
        pdf(self.root/'mixed.pdf',[(595,842),(842,1191),(595,842)])
        raw=(self.root/'mixed.pdf').read_bytes();source=PdfReader(io.BytesIO(raw));source.pages[1].rotate(90)
        ready={'volumes':[{'title':'Том','documents':[
            {'id':'one','type':'Паспорт','name':'Первый','reader':source,'selection':[0,1,2],'count':3},
            {'id':'two','type':'Паспорт','name':'Второй','reader':source,'selection':[0],'count':1}]}]}
        for numbered in (False,True):
            target=self.root/('print'+str(numbered));write_print_folder(self.store,[ready],target,
                {'types':{'Паспорт':'duplex'},'numberPages':numbered})
            files=list((target/'Для принтера').glob('*.pdf'));self.assertEqual(len(files),2)
            for file in files:self.assertEqual(len(PdfReader(file).pages)%2,0)
            a4=next(f for f in files if f.name.startswith('А4'))
            self.assertEqual(len(PdfReader(a4).pages),6) # three one-page segments, each with a blank back
            self.assertEqual(len(list((target/'По порядку сборки').glob('*.pdf'))),2)
            self.assertTrue((target/'Порядок комплектации.pdf').is_file())
        self.assertEqual(source.pages[1].rotation,90)
        self.assertEqual((self.root/'mixed.pdf').read_bytes(),raw)
    def test_print_failure_publishes_no_partial_folder(self):
        pdf(self.root/'one.pdf',[(595,842)]);reader=PdfReader(self.root/'one.pdf')
        ready={'volumes':[{'title':'Том','documents':[{'id':'1','name':'Документ','reader':reader,'selection':[0]}]}]}
        target=self.root/'failed'
        with patch('print_export.render_html',side_effect=RuntimeError('render failed')):
            with self.assertRaises(RuntimeError):write_print_folder(self.store,[ready],target)
        self.assertFalse(target.exists())
