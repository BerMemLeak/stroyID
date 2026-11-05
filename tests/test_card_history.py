"""Card timelines are immutable, multi-writer and independent from projections."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from folder_store import Store,encode,digest
from test_storage import state,material

class CardHistoryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=Store(self.root/'one');self.store.actor='ПК-1'
  s=state();s['lib']['base']=[material('m','Труба'),material('other','Другая')];self.store.save(s,0)
 def tearDown(self):self.temp.cleanup()
 def edit(self,maker,store=None):
  store=store or self.store;s=store.load()['state'];s['lib']['base'][0]['maker']=maker
  return store.save(s,store.revision)['state']
 def versions(self):return self.store.card_history('base:m')['versions']
 def attach(self,data):
  path=self.root/'file.pdf';path.write_bytes(data);s=self.store.load()['state'];asset=self.store.import_file(path)
  s['lib']['base'][0]['docs']=[{'id':'d','type':'Паспорт','num':'1','date':'2026-10-19','file':asset['name'],'fileKey':asset['id']}]
  return self.store.save(s,self.store.revision)['state']
 def sync(self,source,target):
  for folder in ('events_dir','blobs'):
   for file in getattr(source,folder).glob('*'):
    if file.is_file():shutil.copy2(file,getattr(target,folder)/file.name)
  markers=source.service/'Удалённые версии'
  if markers.exists():shutil.copytree(markers,target.service/'Удалённые версии',dirs_exist_ok=True)
 def test_metadata_changes_do_not_copy_pdf_and_noop_does_not_make_version(self):
  self.attach(b'original');self.edit('Завод');vs=self.versions();count=len(vs)
  self.store.save(self.store.load()['state'],self.store.revision)
  self.assertEqual(len(self.versions()),count)
  history=self.store.path(self.store.paths['base:m']).parent/'История версий'
  self.assertEqual(len(list(history.rglob('*.pdf'))),1)
  self.assertEqual(len(list(history.glob('Версия *'))),count)
  self.assertEqual(len(list(self.store.backups.glob('*.json'))),1)
 def test_renaming_an_unchanged_pdf_does_not_duplicate_history_bytes(self):
  self.attach(b'same');s=self.store.load()['state'];s['lib']['base'][0]['docs'][0]['num']='New number'
  self.store.save(s,self.store.revision)
  history=self.store.path(self.store.paths['base:m']).parent/'История версий'
  self.assertEqual(len(list(history.rglob('*.pdf'))),1)
 def test_restoring_then_returning_creates_new_nodes_with_old_files(self):
  self.attach(b'first');first=self.versions()[0]['id'];self.attach(b'second');second=self.versions()[0]['id']
  result=self.store.restore_card_version('base:m',first,heads=self.store.heads['base:m'],user='Илья')
  doc=result['state']['lib']['base'][0]['docs'][0];self.assertEqual(self.store.asset_path(doc['fileKey'])[0].read_bytes(),b'first')
  restored=self.versions()[0];self.assertEqual(restored['action'],'restore');self.assertEqual(restored['sourceVersion'],first);self.assertEqual(restored['by'],'Илья')
  result=self.store.restore_card_version('base:m',second)
  doc=result['state']['lib']['base'][0]['docs'][0];self.assertEqual(self.store.asset_path(doc['fileKey'])[0].read_bytes(),b'second')
  self.assertTrue({first,second}<={v['id'] for v in self.versions()})
  self.assertEqual(result['state']['lib']['base'][1]['name'],'Другая')
 def test_read_only_preview_does_not_change_head_or_live_file(self):
  self.attach(b'old');old=self.versions()[0]['id'];self.attach(b'new');heads=copy.deepcopy(self.store.heads)
  preview=self.store.card_version('base:m',old);path=self.store.path(preview['files'][0]['key']);self.assertEqual(path.read_bytes(),b'old')
  self.assertEqual(self.store.heads,heads)
  live=self.store.load()['state']['lib']['base'][0]['docs'][0];self.assertEqual(self.store.asset_path(live['fileKey'])[0].read_bytes(),b'new')
 def test_four_offline_writers_choose_one_and_decision_replicates(self):
  writers=[]
  for n in range(4):
   folder=self.root/('peer'+str(n));shutil.copytree(self.store.root,folder);peer=Store(folder);peer.actor='ПК-'+str(n+2);writers.append(peer)
   s=peer.load()['state'];s['lib']['base'][0]['maker']='Вариант '+str(n);peer.save(s,peer.revision)
  for peer in writers:self.sync(peer,self.store)
  result=self.store.load();conflict=next(c for c in result['conflicts'] if c['key']=='base:m');self.assertEqual(len(conflict['versions']),4)
  snapshot=copy.deepcopy(result['state']);snapshot['lib']['base'][0]['maker']='Запрещено'
  with self.assertRaises(ValueError):self.store.save(snapshot,self.store.revision)
  chosen=conflict['versions'][2]['id'];self.store.restore_card_version('base:m',chosen,heads=self.store.heads['base:m'],resolve=True)
  self.assertFalse(self.store.conflicts);self.assertEqual(len(self.versions()),6)
  for peer in writers:
   self.sync(self.store,peer);r=peer.load();self.assertFalse(r['conflicts']);self.assertEqual(r['state']['lib']['base'][0]['maker'],self.store.latest['base:m']['data']['maker'])
 def test_fresh_offline_branch_after_resolution_is_not_lost(self):
  folder=self.root/'peer';shutil.copytree(self.store.root,folder);peer=Store(folder);s=peer.load()['state']
  self.edit('A');self.store.restore_card_version('base:m',self.versions()[-1]['id'])
  s['lib']['base'][0]['maker']='Поздняя ветка';peer.save(s,peer.revision);self.sync(peer,self.store)
  self.assertEqual(len(self.store.load()['conflicts'][0]['versions']),2)
 def test_prune_owner_transfers_shared_pdf_and_syncs_tombstone(self):
  self.attach(b'shared');owner=self.versions()[0]['id'];self.edit('Дата без PDF');head=self.versions()[0]['id']
  oldevent=copy.deepcopy(self.store.events[owner]);folder=self.root/'peer';shutil.copytree(self.store.root,folder);peer=Store(folder);peer.load()
  preview=self.store.delete_card_versions('base:m',[owner],preview=True);self.assertEqual(preview['keptFiles'],1)
  self.store.delete_card_versions('base:m',[owner]);self.assertNotIn(owner,{v['id'] for v in self.versions()})
  source,_=self.store.history_asset('base:m',head,digest_bytes(b'shared'));self.assertEqual(source.read_bytes(),b'shared')
  history=self.store.path(self.store.paths['base:m']).parent/'История версий';self.assertEqual(len(list(history.rglob('*.pdf'))),1)
  self.sync(self.store,peer);self.assertNotIn(owner,{v['id'] for v in peer.card_history('base:m')['versions']})
  # A delayed original event and JSON projection cannot resurrect a pruned state.
  (self.store.events_dir/(owner+'.json')).write_bytes(encode(oldevent));self.store.path(self.store.paths['base:m']).write_bytes(encode(oldevent['record']['data']))
  self.assertFalse(self.store.load()['conflicts']);self.assertEqual(self.store.latest['base:m']['data']['maker'],'Дата без PDF')
  self.assertTrue(self.store.events[owner]['pruned'])
 def test_prune_unique_pdf_reclaims_cache_and_history_but_current_cannot_be_deleted(self):
  self.attach(b'A'*4096);old=self.versions()[0]['id'];sha=digest_bytes(b'A'*4096);self.attach(b'B'*2048)
  info=self.store.delete_card_versions('base:m',[old],preview=True);self.assertGreater(info['bytes'],4096)
  self.store.delete_card_versions('base:m',[old]);self.assertFalse((self.store.blobs/sha).exists())
  with self.assertRaises(ValueError):self.store.card_version('base:m',old)
  with self.assertRaises(ValueError):self.store.delete_card_versions('base:m',self.store.heads['base:m'])
 def test_manual_backup_pins_old_pdf(self):
  self.attach(b'manual');old=self.versions()[0]['id'];backup=self.store.backup('Вручную');self.attach(b'current')
  self.store.delete_card_versions('base:m',[old]);self.assertTrue((self.store.blobs/digest_bytes(b'manual')).is_file());self.assertTrue(Path(backup['path']).is_file())
  self.store.restore(backup['path']);doc=self.store.load()['state']['lib']['base'][0]['docs'][0]
  self.assertEqual(self.store.asset_path(doc['fileKey'])[0].read_bytes(),b'manual')
 def test_stale_choices_are_rejected_and_pending_files_do_not_restore(self):
  self.attach(b'old');old=self.versions()[0]['id'];heads=copy.deepcopy(self.store.heads['base:m']);self.attach(b'new')
  with self.assertRaises(ValueError):self.store.restore_card_version('base:m',old,heads=heads)
  with self.assertRaises(ValueError):self.store.delete_card_versions('base:m',[old],heads=heads)
  sha=digest_bytes(b'old');(self.store.blobs/sha).unlink()
  for file in self.store.root.rglob('*.pdf'):
   if file.read_bytes()==b'old':file.unlink()
  version=self.store.card_version('base:m',old);self.assertFalse(version['ready'])
  with self.assertRaisesRegex(ValueError,'Ожидаются'):self.store.restore_card_version('base:m',old)
 def test_failed_projection_retry_is_idempotent_on_one_pc(self):
  s=self.store.load()['state'];base=copy.deepcopy(s);heads=copy.deepcopy(self.store.base_heads);s['lib']['base'][0]['maker']='Сохранено'
  from workspace_store import atomic as original
  once=[]
  def fail_projection(path,data):
   if Path(path).name=='Материал.json' and not once:once.append(1);raise OSError('Simulated crash after event commit')
   return original(path,data)
  with patch('workspace_store.atomic',side_effect=fail_projection):
   with self.assertRaises(OSError):self.store.save(s,self.store.revision,base,heads)
  self.store.save(s,self.store.revision,base,heads)
  self.assertFalse(self.store.conflicts);self.assertEqual(len(self.versions()),2)
 def test_restart_rename_and_history_numbers_survive_pruning(self):
  self.attach(b'pdf');old=self.versions()[0]['id'];self.edit('Новый');last_number=self.versions()[0]['number'];self.store.delete_card_versions('base:m',[old])
  self.store=Store(self.store.root);self.edit('Ещё');self.assertEqual(self.versions()[0]['number'],last_number+1)
  s=self.store.load()['state'];s['lib']['base'][0]['name']='Насос';oldpath=self.store.path(self.store.paths['base:m']).parent;self.store.save(s,self.store.revision)
  self.assertFalse(oldpath.exists());self.assertTrue((self.store.path(self.store.paths['base:m']).parent/'История версий').is_dir())
 def test_compacted_node_arriving_before_new_child_keeps_card_readonly(self):
  self.attach(b'old');old=self.versions()[0]['id'];folder=self.root/'offline-stub';shutil.copytree(self.store.root,folder);peer=Store(folder);peer.load()
  self.edit('Новое');self.store.delete_card_versions('base:m',[old])
  shutil.copy2(self.store.events_dir/(old+'.json'),peer.events_dir/(old+'.json'))
  loaded=peer.load();self.assertEqual(loaded['state']['lib']['base'][0]['name'],'Труба');self.assertIn('base:m',peer._history_pending_keys)
  loaded['state']['lib']['base'][0]['maker']='Не доставлено'
  with self.assertRaises(ValueError):peer.save(loaded['state'],peer.revision)
  self.sync(self.store,peer);loaded=peer.load();self.assertFalse(peer._history_pending_keys);self.assertEqual(loaded['state']['lib']['base'][0]['maker'],'Новое')
 def test_tombstone_arriving_before_new_head_waits(self):
  self.attach(b'old');old=self.versions()[0]['id'];folder=self.root/'offline';shutil.copytree(self.store.root,folder);peer=Store(folder);peer.load()
  self.edit('Новое');self.store.delete_card_versions('base:m',[old]);shutil.copytree(self.store.service/'Удалённые версии',peer.service/'Удалённые версии')
  # Marker alone must not hide the peer's still-current card.
  self.assertEqual(peer.load()['state']['lib']['base'][0]['name'],'Труба')
  self.assertIn(old,{v['id'] for v in peer.card_history('base:m')['versions']})
  self.sync(self.store,peer);self.assertNotIn(old,{v['id'] for v in peer.card_history('base:m')['versions']})

def digest_bytes(data):
 import hashlib
 return hashlib.sha256(data).hexdigest()
