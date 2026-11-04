"""Scoped passports, explicit preview mutations and unchanged-file work regression checks."""
import io,copy,json,tempfile,unittest,time
from pathlib import Path
from pypdf import PdfWriter
from stroyid.infrastructure.storage import Store
from stroyid.domain.migrations import migrate
from test_workspace_v8 import state,project,system
class ScopeAndSpeed(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=Store(self.root/'base')
 def tearDown(self):self.tmp.cleanup()
 def fixture(self):
  s=state();p=project();p['systems']=[system('s1','e1')];s['projects']=[p];w=PdfWriter();w.add_blank_page(600,800);f=self.root/'source.pdf';w.write(f);asset=self.store.import_file(f)
  p['materials']=[{'id':'own','baseId':'','name':'Объектная труба','category':'Труба','brand':'Сталь','maker':'Завод','note':'','docs':[{'id':'private-doc','type':'Паспорт','num':'1','date':'2026-10-12','file':asset['name'],'fileKey':asset['id'],'pages':1}]}]
  return self.store.save(s,0)['state']
 def test_object_passport_stays_editable_and_private_after_every_save(self):
  s=self.fixture();self.assertEqual(s['lib']['base'],[]);m=s['projects'][0]['materials'][0];self.assertEqual(m['scope'],'object');self.assertTrue(m['docs'][0]['fileKey'].startswith('УТК Боец/'));m['maker']='Новый завод';r=self.store.save(s,0)['state'];self.assertEqual(r['projects'][0]['materials'][0]['maker'],'Новый завод');self.assertEqual(r['lib']['base'],[])
 def test_promotion_moves_one_working_file_to_global_and_preserves_reference(self):
  s=self.fixture();m=s['projects'][0]['materials'][0];old=m['docs'][0]['fileKey'];b=copy.deepcopy(m);b['id']='global';b['scope']='common';s['lib']['base'].append(b);m['baseId']='global';m['docs']=[];r=self.store.save(s,0)['state'];new=r['lib']['base'][0]['docs'][0]['fileKey'];self.assertTrue(new.startswith('Справочники/'));self.assertFalse(self.store.path(old).exists());self.assertEqual(r['projects'][0]['materials'][0]['docs'],[]);self.assertEqual(r['projects'][0]['materials'][0]['baseId'],'global')
 def test_project_rename_removes_deep_empty_scaffolding_but_keeps_files_and_history(self):
  s=self.fixture();pid=s['projects'][0]['id'];old=self.store.path(self.store.paths['projects:'+pid]).parent
  (old/'Старый раздел'/'Пустой подраздел'/'Схемы').mkdir(parents=True)
  s['projects'][0]['name']='Новое название';result=self.store.save(s,self.store.revision)
  self.assertFalse(result['warnings']);self.assertFalse(result['conflicts']);self.assertFalse(old.exists())
  m=result['state']['projects'][0]['materials'][0]
  self.assertTrue(self.store.asset_path(m['docs'][0]['fileKey'])[0].is_file())
  current=self.store.path(self.store.paths['projects:'+pid]).parent
  (current/'Ручные файлы').mkdir();(current/'Ручные файлы'/'note.txt').write_text('keep')
  result['state']['projects'][0]['name']='Ещё одно название';self.store.save(result['state'],self.store.revision)
  self.assertEqual((current/'Ручные файлы'/'note.txt').read_text(),'keep')
 def test_reopen_cleans_previously_left_empty_project_tree_only(self):
  s=self.fixture();pid=s['projects'][0]['id'];old=self.store.path(self.store.paths['projects:'+pid]).parent
  s['projects'][0]['name']='Переименованный объект';self.store.save(s,self.store.revision)
  (old/'Пустая ветка'/'Вложенная папка').mkdir(parents=True)
  unrelated=self.store.root/'Моя пустая папка';unrelated.mkdir()
  again=Store(self.store.root);loaded=again.load()
  self.assertFalse(old.exists());self.assertTrue(unrelated.exists());self.assertFalse(loaded['warnings'])
  again.close()
 def test_rename_retries_empty_folder_after_temporary_windows_lock(self):
  from unittest.mock import patch
  s=self.fixture();old=self.store.path(self.store.paths['projects:p']).parent
  original=Path.rmdir;locked=[True]
  def rmdir(path):
   if path==old and locked[0]:raise PermissionError(13,'Simulated Windows directory watcher lock',str(path))
   return original(path)
  with patch.object(Path,'rmdir',rmdir):
   s['projects'][0]['name']='После переименования';result=self.store.save(s,self.store.revision)
   self.assertFalse(result['conflicts']);self.assertTrue(old.exists());self.assertEqual(list(old.iterdir()),[])
   locked[0]=False
   self.store.load()
   self.assertFalse(old.exists(),'Failed cleanup was cached and never retried')
 def test_unchanged_refresh_does_not_hash_documents_or_parse_json_again(self):
  self.fixture();self.store.load();before=self.store.metrics.copy();cpu=time.process_time()
  for _ in range(10):self.store.load()
  self.assertEqual(self.store.metrics['hashed_files'],before['hashed_files']);self.assertEqual(self.store.metrics['parsed_json'],before['parsed_json']);self.assertLess(time.process_time()-cpu,2)
 def test_cache_invalidates_on_external_file_replacement(self):
  s=self.fixture();path=self.store.path(s['projects'][0]['materials'][0]['docs'][0]['fileKey']);before=self.store.hash_file(path);path.write_bytes(path.read_bytes()+b'\n% changed');self.assertNotEqual(self.store.hash_file(path),before)
 def test_preview_delete_and_restore_never_persist_until_explicit_save(self):
  saved=self.fixture();metrics=self.store.metrics.copy();r=self.store.move_trash({'ent':'sys','id':'s1','preview':True,'state':saved});self.assertTrue(r['preview']);self.assertEqual(r['state']['projects'][0]['systems'],[]);self.assertEqual(self.store.metrics['saves'],metrics['saves']);self.assertEqual(len(self.store.load()['state']['projects'][0]['systems']),1)
  rr=self.store.restore_trash({'id':r['state']['trash'][0]['id'],'preview':True,'state':r['state']});self.assertEqual(len(rr['state']['projects'][0]['systems']),1);self.assertEqual(self.store.metrics['saves'],metrics['saves'])
 def test_migration_marks_existing_common_passports_for_review_without_guessing(self):
  s=self.fixture();s['meta']['folderModel']=8;s['meta'].pop('materialScopeVersion');s['lib']['base']=[{'id':'shared','name':'Паспорт','docs':[]}];r=migrate(s);self.assertTrue(r['meta']['passportReviewPending']);self.assertEqual(r['projects'][0]['materials'][0]['baseId'],'');self.assertEqual(r['lib']['base'][0]['id'],'shared');self.assertEqual(migrate(r),r)
 def fixture_snapshot(self,s):
  result=copy.deepcopy(s);result['projects'][0]['materials'][0]['maker']='Завод';return result
 def test_owned_archived_quality_document_is_protected_and_portable(self):
  import zipfile
  s=self.fixture();r=self.store.move_trash({'ent':'mat','id':'own','path':'docs','row':'private-doc'})['state'];tid=r['trash'][0]['id']
  with self.assertRaisesRegex(ValueError,'используется'):self.store.purge_trash({'id':tid})
  target=self.root/'portable.zip';self.store.portable_export(r,target)
  with zipfile.ZipFile(target) as z:z.extractall(self.root/'other')
  dest=Store(self.root/'other/СтройИД');loaded=dest.load();self.assertFalse(loaded['warnings']);doc=loaded['state']['trash'][0]['item'];self.assertEqual(doc['id'],'private-doc');self.assertTrue(dest.asset_path(doc['fileKey'])[0].exists())
 def test_all_trash_can_be_purged_together_when_only_deleted_objects_reference_passport(self):
  s=self.fixture();b=copy.deepcopy(s['projects'][0]['materials'][0]);b.update(id='b',scope='common');s['lib']['base']=[b];s['projects'][0]['materials'][0].update(baseId='b',docs=[]);self.store.save(s,0);self.store.move_trash({'ent':'proj','id':'p'});self.store.move_trash({'ent':'base','id':'b'});r=self.store.purge_trash({'all':True});self.assertEqual(r['state']['trash'],[])
if __name__=='__main__':unittest.main()
