"""Accept Python's current installer identity and reject unrelated signers."""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(sys.platform == 'win32' or not shutil.which('bash'), 'Requires native bash')
class PythonInstallerIdentityTests(unittest.TestCase):
    def verify(self, certificate_chain):
        return subprocess.run(['bash', '-c',
                               'source "$1"; python_installer_identity_is_psf "$2"',
                               'bootstrap-test', str(ROOT/'tools/verify_python_macos.sh'), certificate_chain],
                              capture_output=True, text=True, timeout=10).returncode

    def test_current_python_foundation_installer_is_accepted(self):
        self.assertEqual(self.verify('''Signed with a trusted timestamp on: 2026-09-30 20:18:51 +0000
   Certificate Chain:
    1. Developer ID Installer: Python Software Foundation (BMM5U3QVKW)
       Expires: 2030-05-21 16:16:18 +0000
    2. Developer ID Certification Authority
    3. Apple Root CA'''), 0)

    def test_other_signers_and_non_leaf_identity_are_rejected(self):
        for identity in [
            '1. Developer ID Installer: Python Software Foundation (DJ3H93M7VJ)',
            '1. Developer ID Installer: Other Developer (BMM5U3QVKW)',
            '1. Developer ID Installer: Fake Python Software Foundation (BMM5U3QVKW)',
            '1. Developer ID Installer: Other Developer (AAAAAAAAAA)\n'
            '2. Developer ID Installer: Python Software Foundation (BMM5U3QVKW)',
            '',
        ]:
            with self.subTest(identity=identity):
                self.assertNotEqual(self.verify(identity), 0)
