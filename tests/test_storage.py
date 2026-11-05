import copy,json,shutil,tempfile,unittest,zipfile,hashlib,sqlite3
from pathlib import Path
from unittest.mock import patch
from stroyid.infrastructure.storage import Store,encode

def state(name='Объект'):return {'meta':{'v':30,'name':name},'projects':[],'ui':{},'locks':{},'lib':{k:[] for k in ('orgs','people','orders','base','profiles','templates')}}
def material(i,n):return {'id':i,'name':n,'docs':[],'category':'','brand':'','maker':'','note':''}
class StorageTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=Store(self.root/'one')
 def tearDown(self):self.tmp.cleanup()
 def init(self):
  s=state();s['lib']['base']=[material('m1','Труба'),material('m2','Кабель')];return self.store.save(s,0)['state']
 def test_restart_no_sqlite(self):
  self.init();self.assertEqual(len(Store(self.store.root).load()['state']['lib']['base']),2);self.assertFalse((self.store.root/'stroiid.sqlite3').exists())
 def test_readable_source_copy(self):
  s=self.init();f=self.root/'Паспорт трубы.pdf';f.write_bytes(b'original');a=self.store.import_file(f);s['lib']['base'][0]['docs']=[{'id':'d','type':'Паспорт','num':'12','date':'2026-10-04','file':a['name'],'fileKey':a['id']}];r=self.store.save(s,1);p,_=self.store.asset_path(r['state']['lib']['base'][0]['docs'][0]['fileKey']);self.assertEqual(p.name,'Паспорт_Труба_12_2026_10_04.pdf');self.assertIn('Труба',str(p));self.assertTrue((p.parent/'Материал.json').exists());f.unlink();self.assertEqual(p.read_bytes(),b'original')
 def test_external_file_appears_once(self):
  self.init();f=self.store.path(self.store.paths['base:m1']).parent;(f/'Сертификат.pdf').write_bytes(b'pdf')
  for _ in range(2):self.assertEqual(len(self.store.load()['state']['lib']['base'][0]['docs']),1)
 def test_new_material_directory(self):
  self.init();p=self.store.root/'Справочники'/'Материалы и паспорта'/'Насос';p.mkdir();(p/'Паспорт.pdf').write_bytes(b'pdf');r=self.store.load();self.assertEqual(len(next(m for m in r['state']['lib']['base'] if m['name']=='Насос')['docs']),1)
 def test_corrupt_json_isolated_and_repaired(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);p.write_text('{broken');r=self.store.load();self.assertTrue(any(w.get('key')=='base:m1' for w in r['warnings']));self.assertEqual(len(r['state']['lib']['base']),2);v=copy.deepcopy(self.store.latest['base:m1']['data']);v['name']='Исправлено';self.store.repair('base:m1',v);self.assertEqual(json.loads(p.read_text())['name'],'Исправлено');self.assertFalse((self.store.service/'Повреждённые JSON').exists())
 def test_wrong_field_type_is_isolated(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);v=json.loads(p.read_text());v['name']=None;p.write_bytes(encode(v));r=self.store.load();self.assertTrue(r['warnings']);self.assertEqual(r['state']['lib']['base'][0]['name'],'Труба')
 def test_external_json_edit(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);v=json.loads(p.read_text());v['maker']='Завод';p.write_bytes(encode(v));self.assertEqual(self.store.load()['state']['lib']['base'][0]['maker'],'Завод')
 def test_path_escape_rejected(self):
  with self.assertRaises(ValueError):self.store.asset_path('../secret')
 def test_deleted_doc_not_resurrected(self):
  self.init();p=self.store.path(self.store.paths['base:m1']).parent;(p/'Паспорт.pdf').write_bytes(b'one');s=self.store.load()['state'];s['lib']['base'][0]['docs']=[];self.store.save(s,0);self.assertEqual(self.store.load()['state']['lib']['base'][0]['docs'],[])
 def test_rename_moves_documents_and_card(self):
  s=self.init();old=self.store.path(self.store.paths['base:m1']);(old.parent/'Паспорт.pdf').write_bytes(b'one');s=self.store.load()['state'];s['lib']['base'][0]['name']='Насос';r=self.store.save(s,0);d=r['state']['lib']['base'][0]['docs'][0];p,_=self.store.asset_path(d['fileKey']);self.assertIn('Насос',str(p));self.assertEqual(p.read_bytes(),b'one');self.assertFalse(old.exists())
 def test_legacy_sqlite_migration(self):
  root = self.root / 'legacy'
  root.mkdir()
  legacy = root / 'stroiid.sqlite3'
  db = sqlite3.connect(legacy)
  try:
   db.executescript('CREATE TABLE workspace(id INTEGER,payload TEXT);CREATE TABLE assets(id TEXT,name TEXT);')
   db.execute('INSERT INTO workspace VALUES(1,?)', (json.dumps(state('Прежняя база')),))
   db.commit()
  finally:
   db.close()

  # Retain the connection so SQLite cannot close it through garbage collection.
  reader = sqlite3.connect(legacy.as_uri() + '?mode=ro', uri=True)
  try:
   with patch('stroyid.infrastructure.storage.legacy.sqlite3.connect', return_value=reader):
    store = Store(root)
   with self.assertRaises(sqlite3.ProgrammingError):
    reader.execute('SELECT 1')
   self.assertFalse(legacy.exists())
   loaded = store.load()
   self.assertEqual(loaded['state']['meta']['name'], 'Прежняя база')
   self.assertFalse(loaded['warnings'])
  finally:
   reader.close()

 def test_shared_material_references_single_library_file(self):
  s=self.init();f=self.root/'Паспорт трубы.pdf';f.write_bytes(b'original');a=self.store.import_file(f)
  s['lib']['base'][0]['docs']=[{'id':'d','type':'Паспорт','num':'','date':'','file':a['name'],'fileKey':a['id']}]
  s=self.store.save(s,0)['state'];s['projects']=[{'id':'p','name':'Котельная','short':'Котельная','systems':[],'materials':[{'id':'mat','baseId':'m1','name':'','docs':[]}],'journals':[],'surveys':[],'opsDocs':[]}]
  r=self.store.save(s,0);m=r['state']['projects'][0]['materials'][0];self.assertEqual(m['name'],'Труба');self.assertEqual(m['baseId'],'m1');self.assertEqual(m['docs'],[]);doc=r['state']['lib']['base'][0]['docs'][0];path,_=self.store.asset_path(doc['fileKey']);self.assertIn('Справочники',str(path));self.assertEqual(path.read_bytes(),b'original');self.assertFalse(any(p.suffix=='.pdf' for p in (self.store.root/'Котельная').rglob('*')))
