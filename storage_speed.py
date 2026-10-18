"""Cache unchanged file content using filesystem identity; preserve explicit verification."""
import copy,json
from pathlib import Path
from folder_core import Store as CoreStore
class FastFiles:
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
