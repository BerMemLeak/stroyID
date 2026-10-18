"""Sharing violations: bounded atomic retry plus a real Win32 handle test on Windows."""
import errno,os,tempfile,time,threading,unittest
from pathlib import Path
from unittest.mock import patch
from folder_core import atomic

def locked(code=5):
 e=PermissionError(errno.EACCES,'Проверочная блокировка');e.winerror=code;return e

class WindowsLocks(unittest.TestCase):
 def test_temporary_windows_access_and_sharing_locks_retry_same_complete_file(self):
  for code in (5,32,33):
   with self.subTest(code=code),tempfile.TemporaryDirectory() as root:
    target=Path(root)/'История.json';atomic(target,b'old');replace=os.replace;calls=[]
    def sometimes(source,destination):
     calls.append(Path(source));self.assertEqual(target.read_bytes(),b'old');self.assertEqual(Path(source).read_bytes(),b'complete new')
     if len(calls)<3:raise locked(code)
     return replace(source,destination)
    with patch('folder_core.os.replace',side_effect=sometimes),patch('folder_core.time.sleep') as wait:atomic(target,b'complete new')
    self.assertEqual(target.read_bytes(),b'complete new');self.assertEqual(len(set(calls)),1);self.assertEqual(wait.call_count,2);self.assertFalse(list(Path(root).glob('.sid-*.tmp')))
 def test_permanent_windows_lock_preserves_original_and_cleans_temp(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/'История.json';atomic(target,b'old')
   with patch('folder_core.os.replace',side_effect=locked(32)) as replace,patch('folder_core.time.sleep') as wait:
    with self.assertRaises(PermissionError):atomic(target,b'new')
   self.assertEqual(replace.call_count,9);self.assertEqual(wait.call_count,8);self.assertEqual(target.read_bytes(),b'old');self.assertEqual(list(Path(root).iterdir()),[target])
 def test_other_io_errors_fail_immediately_without_retry(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/'История.json';atomic(target,b'old')
   with patch('folder_core.os.replace',side_effect=OSError(errno.ENOSPC,'No space')) as replace,patch('folder_core.time.sleep') as wait:
    with self.assertRaises(OSError):atomic(target,b'new')
   self.assertEqual(replace.call_count,1);wait.assert_not_called();self.assertEqual(target.read_bytes(),b'old')
 def test_temporary_cleanup_lock_is_retried(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/'История.json';atomic(target,b'old');unlink=Path.unlink;calls=[]
   def cleanup(path,*args,**kwargs):
    calls.append(path)
    if len(calls)==1:raise locked(5)
    return unlink(path,*args,**kwargs)
   with patch('folder_core.os.replace',side_effect=OSError(errno.ENOSPC,'No space')),patch('folder_core.Path.unlink',cleanup),patch('folder_core.time.sleep'):
    with self.assertRaises(OSError) as error:atomic(target,b'new')
   self.assertEqual(error.exception.errno,errno.ENOSPC);self.assertEqual(len(calls),2);self.assertEqual(list(Path(root).iterdir()),[target])
 @unittest.skipUnless(os.name=='nt','native Windows handle check; runs in build_windows.bat')
 def test_real_windows_reader_releases_lock_and_atomic_save_succeeds(self):
  import ctypes
  from ctypes import wintypes
  kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];kernel.CreateFileW.restype=wintypes.HANDLE
  kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/'История.json';atomic(target,b'old')
   handle=kernel.CreateFileW(str(target),0x80000000,3,None,3,0x80,None)
   self.assertNotEqual(handle,ctypes.c_void_p(-1).value)
   def release():time.sleep(.08);kernel.CloseHandle(handle)
   worker=threading.Thread(target=release);worker.start()
   try:atomic(target,b'new')
   finally:worker.join()
   self.assertEqual(target.read_bytes(),b'new');self.assertFalse(list(Path(root).glob('.sid-*.tmp')))
