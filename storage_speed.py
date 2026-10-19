"""Cache unchanged file content using filesystem identity; preserve explicit verification."""
import copy,json,hashlib
from pathlib import Path
from folder_core import Store as CoreStore
class FastFiles:
 def _write_projection(self,path,content):
  """Skip reading unchanged projections; external replacements invalidate by identity."""
  from folder_core import atomic
  path=Path(path);key=str(path);cache=self.__dict__.setdefault('_projection_cache',{})
  signature=hashlib.sha256(content).digest()
  try:stamp=self._stamp(path)
  except FileNotFoundError:stamp=None
  if stamp is not None and cache.get(key)==(stamp,signature):return
  self.metrics['projection_reads']=self.metrics.get('projection_reads',0)+int(stamp is not None)
  if stamp is None or path.read_bytes()!=content:atomic(path,content)
  cache[key]=(self._stamp(path),signature)
 def _stamp(self,path):
  s=Path(path).stat();return (s.st_mtime_ns,s.st_ctime_ns,s.st_size,s.st_ino)
 def hash_file(self,path):
  p=str(Path(path).resolve());stamp=self._stamp(p);cached=self._hash_cache.get(p)
  if cached and cached[0]==stamp:return cached[1]
  value=CoreStore.hash_file(p);self._hash_cache[p]=(stamp,value);self.metrics['hashed_files']+=1
  return value
 def _read_json(self,path):
  p=str(Path(path).resolve());stamp=self._stamp(p);cached=self._json_cache.get(p)
  if cached and cached[0]==stamp:return cached[1]
  data=json.loads(Path(p).read_text('utf-8-sig'));self._json_cache[p]=(stamp,data);self.metrics['parsed_json']+=1
  return data
