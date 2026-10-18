import copy,json,shutil,tempfile,unittest,zipfile,hashlib,sqlite3
from pathlib import Path
from folder_store import Store,encode

def state(name='Объект'):return {'meta':{'v':30,'name':name},'projects':[],'ui':{},'locks':{},'lib':{k:[] for k in ('orgs','people','orders','base','profiles','templates')}}
def material(i,n):return {'id':i,'name':n,'docs':[],'category':'','brand':'','maker':'','note':''}
class StorageTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=Store(self.root/'one')
 def tearDown(self):self.tmp.cleanup()
 def init(self):
  s=state();s['lib']['base']=[material('m1','Труба'),material('m2','Кабель')];return self.store.save(s,0)['state']
 def sync(self,a,b):
  for folder in ('events_dir','blobs'):
   for p in getattr(a,folder).iterdir():
    if not (getattr(b,folder)/p.name).exists():shutil.copy2(p,getattr(b,folder)/p.name)
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
  self.init();p=self.store.path(self.store.paths['base:m1']);p.write_text('{broken');r=self.store.load();self.assertTrue(any(w.get('key')=='base:m1' for w in r['warnings']));self.assertEqual(len(r['state']['lib']['base']),2);v=copy.deepcopy(self.store.latest['base:m1']['data']);v['name']='Исправлено';self.store.repair('base:m1',v);self.assertEqual(json.loads(p.read_text())['name'],'Исправлено');self.assertTrue(list((self.store.service/'Повреждённые JSON').glob('*')))
 def test_wrong_field_type_is_isolated(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);v=json.loads(p.read_text());v['name']=None;p.write_bytes(encode(v));r=self.store.load();self.assertTrue(r['warnings']);self.assertEqual(r['state']['lib']['base'][0]['name'],'Труба')
 def test_external_json_edit(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);v=json.loads(p.read_text());v['maker']='Завод';p.write_bytes(encode(v));self.assertEqual(self.store.load()['state']['lib']['base'][0]['maker'],'Завод')
 def scenario(self,same):
  self.init();shutil.copytree(self.store.root,self.root/'two');other=Store(self.root/'two');a=self.store.load()['state'];b=other.load()['state'];a['lib']['base'][0]['maker']='A';b['lib']['base'][0 if same else 1]['maker']='B';self.store.save(a,1);other.save(b,1);self.sync(self.store,other);self.sync(other,self.store);return other
 def test_different_cards_merge(self):
  other=self.scenario(False)
  for st in [self.store,other]:
   r=st.load();self.assertFalse(r['conflicts']);self.assertEqual([m['maker'] for m in r['state']['lib']['base']],['A','B'])
 def test_offline_same_card_conflict_and_resolution(self):
  other=self.scenario(True);c=next(c for c in self.store.load()['conflicts'] if c['key']=='base:m1');self.assertEqual({v['record']['data']['maker'] for v in c['versions']},{'A','B'});v=next(v for v in c['versions'] if v['record']['data']['maker']=='A');self.store.resolve(c['key'],v['id']);self.sync(self.store,other);self.assertFalse(other.load()['conflicts']);self.assertEqual(other.load()['state']['lib']['base'][0]['maker'],'A')
 def test_delayed_old_projection_ignored(self):
  self.init();p=self.store.path(self.store.paths['base:m1']);old=p.read_bytes();s=self.store.load()['state'];s['lib']['base'][0]['maker']='Новое';self.store.save(s,0);p.write_bytes(old);self.assertEqual(self.store.load()['state']['lib']['base'][0]['maker'],'Новое')
 def test_backups_deduplicate_and_transfer(self):
  s=self.init();p=self.root/'Паспорт.pdf';p.write_bytes(b'one');a=self.store.import_file(p);s['lib']['base'][0]['docs']=[{'id':'d','type':'Паспорт','num':'','date':'','file':a['name'],'fileKey':a['id']}];self.store.save(s,0);b=self.store.backup();count=len(list(self.store.blobs.iterdir()));self.store.backup();self.assertEqual(len(list(self.store.blobs.iterdir())),count);z=self.root/'copy.zip';self.store.export_backup(b['id'],z);other=Store(self.root/'other');r=other.restore(z);d=r['state']['lib']['base'][0]['docs'][0];self.assertEqual(other.asset_path(d['fileKey'])[0].read_bytes(),b'one')
 def test_bad_backup_rejected(self):
  self.init();b=self.store.backup();p=Path(b['path']);s=json.loads(p.read_text());s['records']['root']='0'*64;p.write_bytes(encode(s))
  with self.assertRaises(ValueError):self.store.restore(p)
  self.assertEqual(self.store.load()['state']['meta']['name'],'Объект')
 def test_path_escape_rejected(self):
  with self.assertRaises(ValueError):self.store.asset_path('../secret')
 def test_deleted_doc_not_resurrected(self):
  self.init();p=self.store.path(self.store.paths['base:m1']).parent;(p/'Паспорт.pdf').write_bytes(b'one');s=self.store.load()['state'];s['lib']['base'][0]['docs']=[];self.store.save(s,0);self.assertEqual(self.store.load()['state']['lib']['base'][0]['docs'],[])
 def test_rename_moves_documents_and_card(self):
  s=self.init();old=self.store.path(self.store.paths['base:m1']);(old.parent/'Паспорт.pdf').write_bytes(b'one');s=self.store.load()['state'];s['lib']['base'][0]['name']='Насос';r=self.store.save(s,0);d=r['state']['lib']['base'][0]['docs'][0];p,_=self.store.asset_path(d['fileKey']);self.assertIn('Насос',str(p));self.assertEqual(p.read_bytes(),b'one');self.assertFalse(old.exists())
 def test_legacy_sqlite_migration(self):
  root=self.root/'legacy';root.mkdir();db=sqlite3.connect(root/'stroiid.sqlite3');db.executescript('CREATE TABLE workspace(id INTEGER,payload TEXT);CREATE TABLE assets(id TEXT,name TEXT);');db.execute('INSERT INTO workspace VALUES(1,?)',(json.dumps(state('Прежняя база')),));db.commit();db.close();st=Store(root);self.assertEqual(st.load()['state']['meta']['name'],'Прежняя база');self.assertTrue((root/'_Служебное/Предыдущая структура/stroiid.sqlite3').exists())
 def test_zip_path_traversal_rejected(self):
  self.init();b=self.store.backup();z=self.root/'good.zip';self.store.export_backup(b['id'],z);bad=self.root/'bad.zip'
  with zipfile.ZipFile(z) as src,zipfile.ZipFile(bad,'w') as dst:
   for name in src.namelist():dst.writestr(name,src.read(name))
   dst.writestr('../outside',b'bad')
  with self.assertRaises(ValueError):self.store.restore(bad)
  self.assertFalse((self.store.root.parent/'outside').exists())

 def test_shared_material_references_single_library_file(self):
  s=self.init();f=self.root/'Паспорт трубы.pdf';f.write_bytes(b'original');a=self.store.import_file(f)
  s['lib']['base'][0]['docs']=[{'id':'d','type':'Паспорт','num':'','date':'','file':a['name'],'fileKey':a['id']}]
  s=self.store.save(s,0)['state'];s['projects']=[{'id':'p','name':'Котельная','short':'Котельная','systems':[],'materials':[{'id':'mat','baseId':'m1','name':'','docs':[]}],'journals':[],'surveys':[],'opsDocs':[]}]
  r=self.store.save(s,0);m=r['state']['projects'][0]['materials'][0];self.assertEqual(m['name'],'Труба');self.assertEqual(m['baseId'],'m1');self.assertEqual(m['docs'],[]);doc=r['state']['lib']['base'][0]['docs'][0];path,_=self.store.asset_path(doc['fileKey']);self.assertIn('Справочники',str(path));self.assertEqual(path.read_bytes(),b'original');self.assertFalse(any(p.suffix=='.pdf' for p in (self.store.root/'Котельная').rglob('*')))
