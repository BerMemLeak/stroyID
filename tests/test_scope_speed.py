"""Scoped passports, explicit preview mutations and unchanged-file work regression checks."""
import io,copy,json,tempfile,unittest,time
from pathlib import Path
from pypdf import PdfWriter
from folder_store import Store
from model_v8 import migrate
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
 def test_unchanged_refresh_does_not_hash_documents_or_parse_json_again(self):
  self.fixture();self.store.load();before=self.store.metrics.copy();cpu=time.process_time()
  for _ in range(10):self.store.load()
  self.assertEqual(self.store.metrics['hashed_files'],before['hashed_files']);self.assertEqual(self.store.metrics['parsed_json'],before['parsed_json']);self.assertLess(time.process_time()-cpu,2)
 def test_projection_cache_skips_reads_and_repairs_external_history_changes(self):
  self.fixture();self.store.load();before=self.store.metrics.get('projection_reads',0)
  self.store.load();self.assertEqual(self.store.metrics.get('projection_reads',0),before)
  manifest=next(self.store.root.glob('**/История версий/**/Версия.json'))
  original=manifest.read_bytes();manifest.write_bytes(b'{"broken":true}')
  self.store.load();self.assertEqual(manifest.read_bytes(),original)
 def test_path_plan_computes_each_card_once_with_nested_hierarchy(self):
  from unittest.mock import patch
  s=self.fixture()
  with patch.object(self.store,'_compute_record_path',wraps=self.store._compute_record_path) as compute:
   self.store.save(s,self.store.revision)
  keys=[call.args[0] for call in compute.call_args_list]
  self.assertEqual(len(keys),len(set(keys)))
 def test_cache_invalidates_on_external_file_replacement(self):
  s=self.fixture();path=self.store.path(s['projects'][0]['materials'][0]['docs'][0]['fileKey']);before=self.store.hash_file(path);path.write_bytes(path.read_bytes()+b'\n% changed');self.assertNotEqual(self.store.hash_file(path),before)
 def test_preview_delete_and_restore_never_persist_until_explicit_save(self):
  saved=self.fixture();metrics=self.store.metrics.copy();r=self.store.move_trash({'ent':'sys','id':'s1','preview':True,'state':saved});self.assertTrue(r['preview']);self.assertEqual(r['state']['projects'][0]['systems'],[]);self.assertEqual(self.store.metrics['saves'],metrics['saves']);self.assertEqual(len(self.store.load()['state']['projects'][0]['systems']),1)
  rr=self.store.restore_trash({'id':r['state']['trash'][0]['id'],'preview':True,'state':r['state']});self.assertEqual(len(rr['state']['projects'][0]['systems']),1);self.assertEqual(self.store.metrics['saves'],metrics['saves'])
 def test_migration_marks_existing_common_passports_for_review_without_guessing(self):
  s=self.fixture();s['meta']['folderModel']=8;s['meta'].pop('materialScopeVersion');s['lib']['base']=[{'id':'shared','name':'Паспорт','docs':[]}];r=migrate(s);self.assertTrue(r['meta']['passportReviewPending']);self.assertEqual(r['projects'][0]['materials'][0]['baseId'],'');self.assertEqual(r['lib']['base'][0]['id'],'shared');self.assertEqual(migrate(r),r)
 def test_local_edit_preserves_old_heads_and_detects_remote_conflict(self):
  saved=self.fixture();heads=copy.deepcopy(self.store.base_heads);remote=Store(self.store.root);rs=remote.load()['state'];rs['projects'][0]['materials'][0]['maker']='Другой инженер';remote.save(rs,remote.revision);self.store.load();saved['projects'][0]['materials'][0]['maker']='Мой ввод';r=self.store.save(saved,self.store.revision,base_state=self.fixture_snapshot(saved),base_heads=heads);self.assertTrue(any(c['key']=='materials:own' for c in r['conflicts']))
 def fixture_snapshot(self,s):
  result=copy.deepcopy(s);result['projects'][0]['materials'][0]['maker']='Завод';return result
 def test_corrupt_passport_does_not_block_saving_another_card(self):
  s=self.fixture();path=self.store.path(self.store.paths['materials:own']);path.write_text('{broken');loaded=self.store.load();self.assertTrue(loaded['warnings']);loaded['state']['projects'][0]['name']='Другое название';r=self.store.save(loaded['state'],self.store.revision);self.assertEqual(r['state']['projects'][0]['name'],'Другое название');self.assertTrue(r['warnings'])
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
