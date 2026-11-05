import os,tempfile,unittest,shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from folder_store import atomic,windows_extended_path

@contextmanager
def long_path_temporary_directory():
 # The cleanup must use the same extended Win32 path as the writes.
 # TemporaryDirectory's default cleanup traverses ordinary paths on Windows.
 root=tempfile.mkdtemp()
 root=Path(windows_extended_path(root)) if os.name=='nt' else Path(root)
 try:yield root
 finally:shutil.rmtree(root)

class AtomicPaths(unittest.TestCase):
 def test_long_unicode_document_name_and_nested_path(self):
  with long_path_temporary_directory() as root:
   target=Path(root)/('Объект_'+ 'я'*25)/('Система_'+ 'ю'*25)/('Документы_'+ 'ё'*25)/('п'*110+'.pdf')
   atomic(target,b'old');atomic(target,b'new')
   readable=Path(windows_extended_path(target)) if os.name=='nt' else target
   self.assertEqual(readable.read_bytes(),b'new')
   self.assertFalse(list(target.parent.glob('.sid-*.tmp')))
  self.assertFalse(root.exists())
 def test_failed_replace_preserves_original_and_cleans_temporary_file(self):
  with tempfile.TemporaryDirectory() as root:
   target=Path(root)/'Паспорт.pdf';atomic(target,b'old')
   with patch('folder_store.os.replace',side_effect=OSError('blocked')):
    with self.assertRaises(OSError):atomic(target,b'new')
   self.assertEqual(target.read_bytes(),b'old');self.assertEqual(list(target.parent.iterdir()),[target])
 def test_drive_unc_and_already_extended_windows_paths(self):
  self.assertEqual(windows_extended_path(r'C:\Users\ПК\Паспорт.pdf'),r'\\?\C:\Users\ПК\Паспорт.pdf')
  self.assertEqual(windows_extended_path(r'\\server\share\Паспорт.pdf'),r'\\?\UNC\server\share\Паспорт.pdf')
  self.assertEqual(windows_extended_path(r'\\?\C:\Паспорт.pdf'),r'\\?\C:\Паспорт.pdf')
