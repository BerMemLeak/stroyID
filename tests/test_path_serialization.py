"""Exercise Windows path serialization on every build platform."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from folder_store import Store,encode
from test_storage import state,material

class WindowsSerializedStore(Store):
 def _record_path(self,key,record,records):
  # The library fixtures have no nested parents, so this models the exact
  # Windows boundary without replacing the real filesystem implementation.
  return super()._record_path(key,record,records).replace('/','\\')

class PathSerialization(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=WindowsSerializedStore(self.root/'one')
 def tearDown(self):self.temp.cleanup()
 def initial(self):
  s=state();s['lib']['base']=[material('m1','Труба'),material('m2','Кабель')];return self.store.save(s,0)['state']
 def test_unchanged_cards_never_gain_revisions_from_separator_changes(self):
  s=self.initial();before={k:list(ids) for k,ids in self.store.heads.items()};s['meta']['name']='Новое имя базы';r=self.store.save(s,0)
  self.assertFalse(r['conflicts']);self.assertEqual(self.store.heads['base:m1'],before['base:m1']);self.assertEqual(self.store.heads['base:m2'],before['base:m2'])
 def test_external_valid_edit_survives_save_of_another_card(self):
  s=self.initial();p=self.store.path(self.store.paths['base:m1']);d=json.loads(p.read_text());d['maker']='Из Проводника';p.write_bytes(encode(d));s['meta']['name']='Локальное изменение';r=self.store.save(s,0)
  self.assertFalse(r['conflicts']);self.assertEqual(self.store.load()['state']['lib']['base'][0]['maker'],'Из Проводника')
 def test_offline_distinct_cards_merge_with_windows_serialization(self):
  self.initial();shutil.copytree(self.store.root,self.root/'two');other=WindowsSerializedStore(self.root/'two');a=self.store.load()['state'];b=other.load()['state'];a['lib']['base'][0]['maker']='A';b['lib']['base'][1]['maker']='B';self.store.save(a,0);other.save(b,0)
  for source,target in [(self.store,other),(other,self.store)]:
   for folder in ('events_dir','blobs'):
    for p in getattr(source,folder).iterdir():
     dst=getattr(target,folder)/p.name
     if not dst.exists():shutil.copy2(p,dst)
  for store in (self.store,other):
   r=store.load();self.assertFalse(r['conflicts']);self.assertEqual([m['maker'] for m in r['state']['lib']['base']],['A','B'])
 def test_legacy_backslash_projection_ledger_detects_missing_card(self):
  self.initial();ledger=json.loads(self.store.ledger_path.read_text())
  for item in ledger.values():item['files']=[p.replace('/','\\') for p in item['files']]
  self.store.ledger_path.write_bytes(encode(ledger));missing=self.store.path(self.store.paths['base:m1']);missing.unlink();r=Store(self.store.root).load()
  self.assertTrue(any(w.get('key')=='base:m1' and w.get('missing') for w in r['warnings']));self.assertFalse(missing.exists())
