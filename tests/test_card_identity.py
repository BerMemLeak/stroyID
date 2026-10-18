import copy,json,tempfile,unittest
from pathlib import Path
from folder_store import Store
from test_workspace_v8 import state

class CardIdentity(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'base')
 def tearDown(self):self.temp.cleanup()
 def person(self,ident,name='Новый представитель'):
  return dict(id=ident,fio='ФИО '+ident,fioShort=name,position='',orgId='org',docRole=1,authority='',nrs='',sign='')
 def initial(self):
  s=state();s['lib']['orgs']=[dict(id='org',short='Ремстройтрест')];s['lib']['people']=[self.person('z-first')];return self.store.save(s,0)['state']
 def test_adding_same_title_person_does_not_move_first_or_read_wrong_id(self):
  s=self.initial();old=self.store.paths['people:z-first'];s['lib']['people'].append(self.person('a-second'));r=self.store.save(s,self.store.revision)
  self.assertEqual(r['warnings'],[]);self.assertEqual(self.store.paths['people:z-first'],old);self.assertNotEqual(self.store.paths['people:a-second'],old)
  self.assertEqual([x['id'] for x in r['state']['lib']['people']],['z-first','a-second'])
  for _ in range(3):self.assertEqual(Store(self.store.root).load()['warnings'],[])
 def test_swapping_person_names_writes_correct_projections_before_rescanning(self):
  s=self.initial();s['lib']['people'].append(self.person('a-second','Второй'));s=self.store.save(s,0)['state']
  s['lib']['people'][0]['fioShort']='Второй';s['lib']['people'][1]['fioShort']='Новый представитель';r=self.store.save(s,0)
  self.assertEqual(r['warnings'],[])
  for person in r['state']['lib']['people']:
   d=json.loads(self.store.path(self.store.paths['people:'+person['id']]).read_text());self.assertEqual(d['id'],person['id'])
 def test_unrelated_save_does_not_overwrite_external_valid_json(self):
  s=self.initial();p=self.store.path(self.store.paths['people:z-first']);d=json.loads(p.read_text());d['position']='Из Проводника';p.write_text(json.dumps(d,ensure_ascii=False));s['meta']['name']='Изменена база';self.store.save(s,0)
  self.assertEqual(self.store.load()['state']['lib']['people'][0]['position'],'Из Проводника')
 def test_external_wrong_id_is_still_reported(self):
  self.initial();p=self.store.path(self.store.paths['people:z-first']);d=json.loads(p.read_text());d['id']='bad';p.write_text(json.dumps(d));self.assertTrue(any('Не изменяйте поле id' in w['message'] for w in self.store.load()['warnings']))
 def test_windows_event_paths_reopen_on_another_platform(self):
  self.initial()
  for p in self.store.events_dir.glob('*.json'):
   d=json.loads(p.read_text());d['path']=d['path'].replace('/','\\');p.write_text(json.dumps(d,ensure_ascii=False))
  r=Store(self.store.root).load();self.assertEqual(r['warnings'],[]);self.assertEqual(len(r['state']['lib']['people']),1)

class ExportDiagnostics(unittest.TestCase):
 def test_missing_source_reports_hierarchy_card_path_and_link(self):
  from pdf_export import prepare_export,ExportSourceError
  with tempfile.TemporaryDirectory() as root:
   store=Store(Path(root));store.paths={'admin:empty':'Объект/Общие документы/Новый документ/Карточка.json'}
   plan={'object':'Объект','volumes':[{'title':'Выполнение 1 · Том 1','documents':[{'kind':'pdf','id':'adminempty','name':'Новый документ','sourceLocation':'Объект → Выполнение 1 → Общие документы → Новый документ','sourceRef':'#/p/p/admin','cardKey':'admin:empty'}]}]}
   with self.assertRaises(ExportSourceError) as cm:prepare_export(store,plan)
   error=cm.exception;self.assertIn('Выполнение 1',str(error));self.assertIn('Карточка.json',str(error));self.assertEqual(error.details[0]['ref'],'#/p/p/admin');self.assertEqual(error.details[0]['id'],'adminempty')
   store.close()
