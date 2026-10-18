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


if __name__ == '__main__':
    unittest.main()
