import copy,io,json,tempfile,unittest,zipfile
from pathlib import Path
from pypdf import PdfWriter
from folder_store import Store
from model_v8 import migrate

def state():return {'meta':{'v':30,'name':'База'},'projects':[],'ui':{},'history':[],'trash':[],'lib':{k:[] for k in ('orgs','people','orders','base','profiles','templates')}}
def project():return {'id':'p','name':'УТК Боец','short':'УТК Боец','systems':[],'materials':[],'journals':[],'surveys':[],'opsDocs':[],'admin':[],'executions':[{'id':'e1','name':'Выполнение 1','date':'2026-10-12'},{'id':'e2','name':'Выполнение 2','date':'2026-10-15'}]}
def act(id,eid):return {'id':id,'num':'АОСР-1.1','type':'АОСР','date':'2026-10-12','executionId':eid,'works':'Проходки','place':'Корпус','materials':['m'],'schemes':[],'tests':[],'photos':[],'subs':['sp'],'aikLinks':{},'schemeLinks':[],'testLinks':[],'scan':{'file':'','pages':0}}
def system(id,eid):return {'id':id,'executionId':eid,'code':'ВК','name':'Водоснабжение','cipher':'ВК-001','scheme':{'file':'','pages':0},'acts':[act('a-'+id,eid)],'subprofiles':[{'id':'sp-'+id,'name':'Основной','profileId':'pf','signers':{}}],'aik':[],'journals':[],'sketches':[],'trials':[]}
class WorkspaceV8(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=Store(self.root/'base')
 def tearDown(self):self.tmp.cleanup()
 def pdf(self):
  w=PdfWriter();w.add_blank_page(595,842);b=io.BytesIO();w.write(b);w.close();return b.getvalue()
 def fixture(self):
  s=state();p=project();p['systems']=[system('s1','e1'),system('s2','e2')];p['materials']=[{'id':'m','baseId':'b','name':'Труба','docs':[]}];s['projects']=[p]
  f=self.root/'random.pdf';f.write_bytes(self.pdf());asset=self.store.import_file(f);p['systems'][0]['acts'][0]['schemes']=[{'id':'drawing','name':'Проходки','file':asset['name'],'fileKey':asset['id'],'pages':1}]
  s['lib']['base']=[{'id':'b','name':'Труба','category':'','brand':'','maker':'','note':'','docs':[{'id':'quality','type':'Паспорт','num':'123','date':'2026-10-12','file':asset['name'],'fileKey':asset['id'],'pages':1}]}]
  return self.store.save(s,0)['state']
 def test_legacy_system_splits_without_sharing_card_ids(self):
  s=state();p=project();old=system('shared','e1');old.pop('executionId');old['acts']=[act('a1','e1'),act('a2','e2')];p['systems']=[old]
  for e in p['executions']:e['allocations']=[{'systemId':'shared'}];e['stage']='Подготовлено'
  s['projects']=[p];out=migrate(s);one,two=out['projects'][0]['systems'];self.assertNotEqual(one['id'],two['id']);self.assertNotEqual(one['subprofiles'][0]['id'],two['subprofiles'][0]['id']);self.assertEqual([a['id'] for a in one['acts']],['a1']);self.assertNotEqual(two['acts'][0]['id'],'a2');self.assertEqual(two['acts'][0]['executionId'],'e2');self.assertNotIn('allocations',out['projects'][0]['executions'][0]);self.assertEqual(migrate(out),out)
 def test_names_paths_and_automatic_rename(self):
  s=self.fixture();d=s['projects'][0]['systems'][0]['acts'][0]['schemes'][0];old=d['fileKey'];self.assertEqual(Path(old).name,'Схема_ВК_АОСР_1_1_Проходки.pdf');self.assertTrue(old.startswith('УТК Боец/Выполнение 1/ВК'))
  s['projects'][0]['short']='Боец новый';s['projects'][0]['systems'][0]['code']='ВК1';a=s['projects'][0]['systems'][0]['acts'][0];a['num']='АОСР-2.3';a['schemes'][0]['name']='Стояки';r=self.store.save(s,0)['state'];new=r['projects'][0]['systems'][0]['acts'][0]['schemes'][0]['fileKey'];self.assertIn('Боец новый/',new);self.assertEqual(Path(new).name,'Схема_ВК1_АОСР_2_3_Стояки.pdf');self.assertFalse(self.store.path(old).exists());self.assertEqual(self.store.path(new).read_bytes(),self.pdf())
  self.assertTrue(all(x.name in ('Боец новый','Справочники','_Служебное') for x in self.store.root.iterdir()))
 def test_system_delete_restore_and_collision_are_isolated(self):
  self.fixture();r=self.store.move_trash({'ent':'sys','id':'s1','user':'Егор'})['state'];self.assertEqual([s['id'] for s in r['projects'][0]['systems']],['s2']);tid=r['trash'][0]['id'];r['projects'][0]['systems'].append(system('new','e1'));self.store.save(r,0);restored=self.store.restore_trash({'id':tid})['state'];systems=restored['projects'][0]['systems'];self.assertEqual(len(systems),3);self.assertEqual(next(s for s in systems if s['id']=='s2')['name'],'Водоснабжение');self.assertIn('восстановлено',next(s for s in systems if s['id']=='s1')['name']);file=next(s for s in systems if s['id']=='s1')['acts'][0]['schemes'][0]['fileKey'];self.assertEqual(self.store.asset_path(file)[0].read_bytes(),self.pdf())
 def test_restore_deleted_parents_and_no_automatic_execution_recreation(self):
  self.fixture();r=self.store.move_trash({'ent':'sys','id':'s1'})['state'];tid=r['trash'][0]['id'];self.store.move_trash({'ent':'exec','id':'e1','pid':'p'});self.store.move_trash({'ent':'exec','id':'e2','pid':'p'});r=self.store.load()['state'];self.assertEqual(r['projects'][0]['executions'],[]);self.store.move_trash({'ent':'proj','id':'p'});r=self.store.restore_trash({'id':tid,'restoreParents':True})['state'];self.assertEqual([s['id'] for s in r['projects'][0]['systems']],['s1']);self.assertEqual(r['projects'][0]['executions'][0]['id'],'e1')
 def test_used_passport_cannot_be_purged_and_is_not_copied(self):
  s=self.fixture();r=self.store.move_trash({'ent':'base','id':'b'})['state'];tid=r['trash'][0]['id'];self.assertEqual(r['projects'][0]['materials'][0]['baseId'],'b');self.assertEqual(r['lib']['base'],[])
  with self.assertRaisesRegex(ValueError,'используется'):self.store.purge_trash({'id':tid})
  r['projects'][0]['materials']=[];self.store.save(r,0);self.assertEqual(self.store.purge_trash({'id':tid})['state']['trash'],[])
 def test_explorer_deletion_warns_until_explicit_recovery_even_after_restart(self):
  s=self.fixture();d=s['projects'][0]['systems'][0]['acts'][0]['schemes'][0];file=self.store.path(d['fileKey']);file.unlink();r=Store(self.store.root).load();self.assertTrue(any(w.get('missing') for w in r['warnings']));self.assertFalse(file.exists());r=self.store.load();self.store.recover_missing('acts:a-s1');self.assertEqual(file.read_bytes(),self.pdf());self.assertFalse(self.store.load()['warnings'])
 def test_portable_zip_reopens_in_unrelated_folder_with_shared_passport(self):
  s=self.fixture();s['projects'][0]['executions']=s['projects'][0]['executions'][:1];s['projects'][0]['systems']=s['projects'][0]['systems'][:1];target=self.root/'portable.zip';self.store.portable_export(s,target)
  with zipfile.ZipFile(target) as z:z.extractall(self.root/'another-pc')
  other=Store(self.root/'another-pc/СтройИД');r=other.load();self.assertFalse(r['warnings']);self.assertEqual(len(r['state']['projects'][0]['systems']),1);doc=r['state']['lib']['base'][0]['docs'][0];self.assertEqual(other.asset_path(doc['fileKey'])[0].read_bytes(),self.pdf());self.assertFalse(any(p.suffix=='.pdf' for p in (other.root/'УТК Боец'/'Общие документы'/'Материалы').rglob('*')))
 def test_migrate_real_v07_repository_with_checkpoint_and_borrowed_sheets(self):
  from folder_core import Store as OldStore
  root=self.root/'v07';old=OldStore(root);s=state();p=project();shared=system('shared','e1');shared.pop('executionId');shared['acts']=[act('first','e1'),act('second','e2')];shared['acts'][0]['schemes']=[{'id':'borrowed','name':'Чужой лист','file':'','pages':2}];shared['acts'][1]['schemeLinks']=[{'id':'borrowed','from':2,'to':2}];p['systems']=[shared]
  for e in p['executions']:e['allocations']=[{'systemId':'shared','qty':'12'}]
  s['projects']=[p];s['volCfg']={'p|T2_sp-shared':{'off':['tests'],'order':['aosr','schemes']}};old.save(s,0);old.close();new=Store(root);loaded=new.load();self.assertFalse(loaded['warnings']);self.assertEqual(len(loaded['state']['projects'][0]['systems']),2);second=loaded['state']['projects'][0]['systems'][1];link=second['acts'][0]['schemeLinks'][0];self.assertTrue(any(x['id']==link['id'] for x in second['sketches']));self.assertEqual(loaded['state']['volCfg']['p|e2::T2_'+second['subprofiles'][0]['id']]['off'],['tests']);self.assertTrue(any('Перед переходом' in b['reason'] for b in new.list_backups()));self.assertEqual({x.name for x in root.iterdir()},{'УТК Боец','_Служебное','Справочники'})
 def test_deleted_quality_row_travels_in_portable_archive_and_restores_parent(self):
  self.fixture();r=self.store.move_trash({'ent':'base','id':'b','path':'docs','row':'quality'})['state'];tid=r['trash'][0]['id']
  with self.assertRaisesRegex(ValueError,'используется'):self.store.purge_trash({'id':tid})
  target=self.root/'quality.zip';self.store.portable_export(r,target)
  with zipfile.ZipFile(target) as z:z.extractall(self.root/'quality-portable')
  dest=Store(self.root/'quality-portable/СтройИД');rr=dest.load()['state'];self.assertEqual(rr['trash'][0]['item']['id'],'quality');self.assertEqual(dest.asset_path(rr['trash'][0]['item']['fileKey'])[0].read_bytes(),self.pdf());dest.close()
  self.store.move_trash({'ent':'base','id':'b'});restored=self.store.restore_trash({'id':tid,'restoreParents':True})['state'];self.assertEqual(restored['lib']['base'][0]['docs'][0]['id'],'quality')
 def test_same_title_cards_do_not_overwrite_and_other_execution_is_not_collision(self):
  s=self.fixture();s['lib']['base'].append({'id':'b2','name':'Труба','docs':[]});saved=self.store.save(s,0)['state'];self.assertNotEqual(self.store.paths['base:b'],self.store.paths['base:b2']);self.assertTrue(self.store.path(self.store.paths['base:b']).exists());self.assertTrue(self.store.path(self.store.paths['base:b2']).exists());t=self.store.move_trash({'ent':'sys','id':'s1'})['state']['trash'][0];restored=self.store.restore_trash({'id':t['id']})['state'];self.assertEqual(next(x for x in restored['projects'][0]['systems'] if x['id']=='s1')['name'],'Водоснабжение')
if __name__=='__main__':unittest.main()
