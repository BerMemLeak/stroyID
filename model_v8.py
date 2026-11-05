"""Idempotent migration to independent systems and shared material documents."""
import copy, hashlib

def stable(prefix,*parts):return prefix+hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()[:20]
def remap(value,mapping):
 if isinstance(value,str):return mapping.get(value,value)
 if isinstance(value,list):return [remap(x,mapping) for x in value]
 if isinstance(value,dict):return {mapping.get(k,k):remap(v,mapping) for k,v in value.items()}
 return value

def migrate(state):
 s=copy.deepcopy(state)
 for p in s['projects']+[t['item'] for t in s.get('trash',[]) if t.get('ent')=='proj']:
  if not (p.get('name') or '').strip():p['name']=p.get('short') or ''
  p.pop('short',None)
 if s['meta'].get('folderModel',0)>=8:return normalize_materials(s)
 legacy=s['meta'].get('folderModel',0)<8
 for p in s['projects']:
  p.setdefault('admin',[])
  if not p.get('executions') and (legacy or p['systems']):p['executions']=[{'id':'execution-'+p['id'],'name':'Выполнение 1','date':''}]
  es=p.setdefault('executions',[]);first=es[0]['id'] if es else '';old_systems=p['systems'];new=[]
  for e in es:
   e.setdefault('date','');e.setdefault('name','Выполнение 1')
  for system in old_systems:
   targets=[system.get('executionId')] if system.get('executionId') and not legacy else []
   if not targets:
    targets=[e['id'] for e in es if any(x.get('systemId')==system['id'] for x in e.get('allocations',[])) or any(a.get('executionId')==e['id'] for a in system.get('acts',[]))]
   if not targets:targets=[first]
   for i,eid in enumerate(dict.fromkeys(targets)):
    if eid not in {e['id'] for e in es}:eid=first
    item=copy.deepcopy(system);mapping={}
    if i:
     mapping[item['id']]=stable('s',p['id'],eid,item['id'])
     def ids(x):
      if isinstance(x,dict):
       if x.get('id') and x['id'] not in (system['id'],'system'):mapping[x['id']]=stable('card-',eid,x['id'])
       for v in x.values():ids(v)
      elif isinstance(x,list):
       for v in x:ids(v)
     ids(item)
     item=remap(item,mapping)
    item['executionId']=eid
    if legacy and len(targets)>1:
     item['acts']=[a for a in item.get('acts',[]) if a.get('executionId',first)==eid]
     item['sketches']=[x for x in item.get('sketches',[]) if not x.get('executionId') or x.get('executionId')==eid]
    if legacy and len(targets)>1:
     # Preserve sheets borrowed from an act which now belongs to another execution.
     sources={x['id']:(a,x) for a in system.get('acts',[]) for x in a.get('schemes',[])}
     available={x['id'] for a in item.get('acts',[]) for x in a.get('schemes',[])}|{x['id'] for x in item.get('sketches',[])}|{'system'}
     for a in item.get('acts',[]):
      for link in a.get('schemeLinks',[]):
       source=next((pair for ident,pair in sources.items() if mapping.get(ident,ident)==link['id']),None)
       if link['id'] not in available and source:
        original=source[1];extra=copy.deepcopy(original);extra['id']=stable('borrowed-',eid,original['id']);extra['executionId']=eid
        if not any(x['id']==extra['id'] for x in item.setdefault('sketches',[])):item['sketches'].append(extra)
        link['id']=extra['id'];available.add(extra['id'])
    for sp in system.get('subprofiles',[]):
     oldkey=p['id']+'|T2_'+sp['id'];newkey=p['id']+'|'+eid+'::T2_'+mapping.get(sp['id'],sp['id']);existing=p['id']+'|'+eid+'::T2_'+sp['id']
     cfg=s.get('volCfg',{}).get(existing,s.get('volCfg',{}).get(oldkey))
     if cfg and newkey not in s.setdefault('volCfg',{}):s['volCfg'][newkey]=remap(cfg,{**mapping,**{prefix+k:prefix+v for k,v in mapping.items() for prefix in ('a','c','sk','k','j')}})
    for a in item.get('acts',[]):a['executionId']=eid
    for field in ('sketches','trials'):
     for x in item.get(field,[]):x['executionId']=eid
    item.setdefault('sketches',[]);item.setdefault('trials',[]);new.append(item)
  p['systems']=new
  for e in es:
   for key in ('T1','T3'):
    old=p['id']+'|'+key;dest=p['id']+'|'+e['id']+'::'+key
    if old in s.get('volCfg',{}) and dest not in s['volCfg']:s['volCfg'][dest]=copy.deepcopy(s['volCfg'][old])
  for e in es:
   e.pop('allocations',None);e.pop('stage',None);e.pop('note',None)
 return normalize_materials(s)

def normalize_materials(s):
 old=s['meta'].get('folderModel',0)
 bases={b['id']:b for b in s['lib']['base']}
 bases.update({t['item']['id']:t['item'] for t in s.get('trash',[]) if t.get('ent')=='base'})
 for b in s['lib']['base']:b['scope']='common'
 for p in s['projects']:
  for m in p['materials']:
   bid=m.get('baseId');oldid=m.get('baseSourceId')
   if not bid and oldid in bases:
    def signature(ds):return [(d.get('id'),d.get('fileHash'),d.get('num'),d.get('date')) for d in ds]
    if signature(m.get('docs',[]))==signature(bases[oldid].get('docs',[])):bid=oldid
   if bid and bid in bases:
    m['baseId']=bid;m['name']=bases[bid].get('name','');m['docs']=[];m['scope']='common'
   else:m['scope']='object';m.setdefault('baseId','');m.setdefault('docs',[])
   m.pop('baseSourceId',None)
 if old==8 and not s['meta'].get('materialScopeVersion'):s['meta']['passportReviewPending']=bool(s['lib']['base'])
 s['meta']['materialScopeVersion']=1;s['meta']['folderModel']=9
 return s
