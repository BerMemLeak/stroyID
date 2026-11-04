"""Exercise Windows path serialization on every build platform."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from stroyid.infrastructure.storage import Store,encode
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
