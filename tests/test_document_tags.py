"""Schema coverage and native replacement contracts independent of UI wiring."""
import tempfile,unittest,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
from document_tags import schema,collection_tags
from word_templates import sample_docx,inspect_docx,fill_docx,package,W
ROOT=Path(__file__).resolve().parents[1]
class DocumentTagTests(unittest.TestCase):
 def test_all_builtin_and_sample_tags_have_one_definition(self):
  fields=schema()['fields']
  with tempfile.TemporaryDirectory() as tmp:
   paths=list((ROOT/'ui/reference-templates').glob('*.docx'))
   for section in ['title','reg','aosr','aook','aik','quantity','photos','spj','other']:
    paths.append(sample_docx(section,section,Path(tmp)/(section+'.docx')))
   for p in paths:
    tags=inspect_docx(p.read_bytes())['tags']
    self.assertFalse(set(tags)-fields.keys(),(p,set(tags)-fields.keys()))
    values={t:'MARK-'+t for t in tags if t not in collection_tags()}
    out=fill_docx(p.read_bytes(),Path(tmp)/'filled.docx',values,{})
    self.assertFalse(inspect_docx(out.read_bytes())['tags'],p)
    text=''.join(''.join(ET.fromstring(b).itertext()) for n,b in package(out.read_bytes()).items() if __import__('word_templates').PART.match(n))
    for t,v in values.items():self.assertIn(v,text,(p,t))
 def test_required_and_optional_are_distinct(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=sample_docx('aosr','Акт',Path(tmp)/'source.docx');tags=inspect_docx(p.read_bytes())['tags'];values={t:'' for t in tags}
   with self.assertRaisesRegex(ValueError,'Не заполнены поля'):fill_docx(p.read_bytes(),Path(tmp)/'bad.docx',values)
   for t in tags:
    if schema()['fields'][t]['required']:values[t]='REQUIRED'
   out=fill_docx(p.read_bytes(),Path(tmp)/'ok.docx',values)
   self.assertFalse(inspect_docx(out.read_bytes())['tags'])
 def test_scalar_registry_text_inside_table_is_not_a_repeating_row(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=sample_docx('reg','Реестр',Path(tmp)/'source.docx');parts=package(p.read_bytes());root=ET.fromstring(parts['word/document.xml']);row=root.find('.//{'+W+'}tr')
   text=row.find('.//{'+W+'}t');text.text='{{Реестр.Текст}}';parts['word/document.xml']=ET.tostring(root)
   with zipfile.ZipFile(p,'w') as z:
    for n,b in parts.items():z.writestr(n,b)
   values={t:'MARK' for t in inspect_docx(p.read_bytes())['tags'] if t not in collection_tags()};values['Реестр.Текст']='SUMMARY'
   out=fill_docx(p.read_bytes(),Path(tmp)/'out.docx',values,{'Реестр':[]})
   root=ET.fromstring(package(out.read_bytes())['word/document.xml']);self.assertEqual(len(root.findall('.//{'+W+'}tr')),1);self.assertIn('SUMMARY',''.join(root.itertext()))
