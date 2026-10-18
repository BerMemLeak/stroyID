"""Regression checks for missing native stdout/stderr during Windows builds."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_builder', Path(__file__).resolve().parents[1] / 'tools/build_release.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildLoggingTests(unittest.TestCase):
    def test_native_failure_preserves_both_streams_and_exit_code(self):
        with tempfile.TemporaryDirectory(prefix='СтройИД проверка ') as root:
            args = [sys.executable, '-c', "import sys; print('stdout-marker',flush=True); print('stderr-marker',file=sys.stderr); sys.exit(7)"]
            with self.assertRaises(subprocess.CalledProcessError) as failure:
                builder.command(args, cwd=root, stage='failure', logs=root)
            self.assertEqual(failure.exception.returncode, 7)
            log = (Path(root) / 'failure.log').read_text(encoding='utf-8')
            self.assertIn('stdout-marker', log)
            self.assertIn('stderr-marker', log)

    def test_initialization_error_still_produces_report(self):
        with tempfile.TemporaryDirectory() as root, patch.object(builder, 'ROOT', Path(root)), \
             patch.object(builder.platform, 'platform', side_effect=RuntimeError('diagnostic-marker')):
            self.assertEqual(builder.build(), 1)
            report = json.loads((Path(root) / 'release/build-report.json').read_text())
            self.assertEqual(report['stage'], 'initialization')
            self.assertFalse(report['passed'])
            self.assertIn('diagnostic-marker', report['traceback'])


class PublishExecutableTests(unittest.TestCase):
    def check_publish(self, failures):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, target = root / 'source.exe', root / 'StroyID.exe'
            source.write_bytes(b'new'); target.write_bytes(b'old')
            original_replace = Path.replace
            attempts = []
            def replace(path, destination):
                self.assertEqual(destination, target)
                attempts.append(destination)
                if len(attempts) <= failures:
                    raise PermissionError(5, 'Access denied')
                return original_replace(path, destination)
            with patch.object(Path, 'replace', replace), \
                 patch.object(builder, 'close_running_release') as close, \
                 patch.object(builder.time, 'sleep'):
                if failures >= 11:
                    with self.assertRaisesRegex(PermissionError, 'source.exe'):
                        builder.publish_executable(source, target)
                    self.assertEqual(target.read_bytes(), b'old')
                else:
                    self.assertEqual(builder.publish_executable(source, target), target)
                    self.assertEqual(target.read_bytes(), b'new')
                if failures:
                    close.assert_called_once_with(target)
                else:
                    close.assert_not_called()
            self.assertEqual(len(attempts), min(failures + 1, 11))
            self.assertFalse(list(root.glob('*.tmp')))
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['StroyID.exe', 'source.exe'])

    def test_normal_replacement(self):
        self.check_publish(0)

    def test_close_then_replace_same_path(self):
        self.check_publish(1)

    def test_transient_lock_retried(self):
        self.check_publish(3)

    def test_persistent_lock_keeps_old_release_and_new_source(self):
        self.check_publish(11)

    def test_close_helper_uses_exact_path_and_bounded_timeout(self):
        target = Path('release/StroyID.exe')
        with patch.object(builder.sys, 'platform', 'win32'), patch.object(builder.subprocess, 'run') as run:
            builder.close_running_release(target)
        args = run.call_args.args[0]
        self.assertEqual(args[-2:], ['-Executable', str(target.resolve())])
        self.assertTrue(args[-3].endswith('close_release.ps1'))
        self.assertEqual(run.call_args.kwargs, {'timeout': 25, 'check': True})


if __name__ == '__main__':
    unittest.main()
