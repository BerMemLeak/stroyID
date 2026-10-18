"""Directory subscriptions must detect file edits without holding target files."""
import tempfile,unittest
from pathlib import Path
from PySide6.QtCore import QObject,QCoreApplication,QEvent,QEventLoop,QTimer
from PySide6.QtWidgets import QApplication
from app import Bridge
from folder_store import Store
from test_storage import state,material

class DirectoryWatcher(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'base');s=state();s['lib']['base']=[material('m1','Труба')];self.store.save(s,0)
  self.parent=QObject();self.bridge=Bridge(self.store,self.parent);self.bridge.refresh_watches()
 def tearDown(self):
  self.bridge.watchTimer.stop();self.bridge.metadataTimer.stop();paths=self.bridge.watcher.files()+self.bridge.watcher.directories()
  if paths:self.bridge.watcher.removePaths(paths)
  self.bridge.executor.shutdown(wait=True);self.parent.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.store.close();self.temp.cleanup()
 def test_only_directories_are_registered_in_native_watcher(self):
  self.assertEqual(self.bridge.watcher.files(),[]);self.assertTrue(self.bridge.watcher.directories());self.assertTrue(all(Path(p).is_dir() for p in self.bridge.watcher.directories()))
  card=self.store.path(self.store.paths['base:m1']);self.assertIn(str(card),self.bridge.observedPaths);self.assertIn(card.parent.resolve(),{Path(p).resolve() for p in self.bridge.watcher.directories()})
 def test_in_place_card_edit_is_detected_and_deduplicated(self):
  card=self.store.path(self.store.paths['base:m1']);self.bridge.observedPaths={str(card)};self.bridge.watchStamp=self.bridge.watch_fingerprint();received=[];self.bridge.folderChanged.connect(lambda:received.append(True))
  with card.open('ab') as stream:stream.write(b'\n')
  self.bridge.notify_external_change();self.bridge.notify_external_change();self.assertEqual(received,[True])

 def test_metadata_fallback_detects_edit_without_native_file_signal(self):
  card=self.store.path(self.store.paths['base:m1']);self.bridge.observedPaths={str(card)};self.bridge.watchStamp=self.bridge.watch_fingerprint();received=[];ticks=[];loop=QEventLoop()
  self.bridge.folderChanged.connect(lambda:(received.append(True),loop.quit()));self.bridge.metadataTimer.timeout.connect(lambda:ticks.append(True));self.bridge.metadataTimer.setInterval(20)
  with card.open('ab') as stream:stream.write(b'\n')
  self.bridge.metadataTimer.start();QTimer.singleShot(1000,loop.quit);loop.exec();self.bridge.metadataTimer.stop();self.assertEqual(received,[True]);self.assertTrue(ticks)
