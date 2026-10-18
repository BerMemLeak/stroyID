"""Build and verify a single executable containing Python, Qt and the UI."""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.9.4'


def command(args, timeout=900, cwd=ROOT, stage='command', logs=None):
    logs = Path(logs) if logs is not None else ROOT / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    log_path = logs / (stage + '.log')
    printable = subprocess.list2cmdline([str(x) for x in args])
    print('\nSTAGE: ' + stage + '\n> ' + printable + '\nLOG: ' + str(log_path), flush=True)
    try:
        # Save both streams directly: no dependence on PowerShell transcription.
        with log_path.open('wb') as stream:
            stream.write(('COMMAND: ' + printable + '\nCWD: ' + str(cwd) + '\n').encode('utf-8'))
            stream.flush()
            result = subprocess.run(args, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=timeout, check=False)
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, args)
    finally:
        if log_path.exists():
            lines = log_path.read_text(encoding='utf-8', errors='replace').splitlines()
            print('\n'.join(lines[-120:]), flush=True)


def build():
    output = ROOT / 'release'
    output.mkdir(exist_ok=True)
    report = {'version': VERSION, 'platform': sys.platform, 'python': sys.version,
              'created': datetime.now(timezone.utc).isoformat(), 'passed': False, 'error': None,
              'stage': 'initialization', 'returncode': None}
    status = output / 'build-report.json'
    try:
        report['platform'] = platform.platform()
        report['stage'] = 'unit-tests'
        command([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 120, stage=report['stage'])
        report['stage'] = 'qt-interface'
        command([sys.executable, 'tests/smoke_qt.py'], 120, stage=report['stage'])
        report['stage'] = 'qt-pdf-export'
        command([sys.executable, 'tests/smoke_pdf.py'], 120, stage=report['stage'])
        report['stage'] = 'qt-word-templates'
        command([sys.executable, 'tests/smoke_word.py'], 120, stage=report['stage'])
        report['stage'] = 'qt-folder-workspace'
        command([sys.executable, 'tests/smoke_folders.py'], 120, stage=report['stage'])
        report['stage'] = 'qt-executions-and-frames'
        command([sys.executable, 'tests/smoke_executions.py'], 120, stage=report['stage'])
        report['stage'] = 'qt-manual-save-and-idle'
        command([sys.executable,'tests/smoke_manual.py'],150,stage=report['stage'])
        report['stage'] = 'qt-local-regressions'
        command([sys.executable,'tests/smoke_regressions.py'],150,stage=report['stage'])
        report['stage'] = 'qt-save-locks'
        command([sys.executable,'tests/smoke_save_locks.py'],150,stage=report['stage'])
        report['stage'] = 'pyinstaller'
        command([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                 '--distpath', 'dist-onefile', 'StroyID.spec'], stage=report['stage'])
        filename = 'StroyID.exe' if sys.platform == 'win32' else 'StroyID'
        executable = ROOT / 'dist-onefile' / filename
        test_report = output / 'packaged-self-test.json'
        test_report.unlink(missing_ok=True)
        # Prove that the executable runs after copying it alone into an otherwise empty folder.
        with tempfile.TemporaryDirectory(prefix='stroiid-onefile-proof-') as isolated:
            isolated = Path(isolated)
            copied = isolated / filename
            shutil.copy2(executable, copied)
            report['stage'] = 'onefile-self-test'
            command([str(copied), '--self-test', str(test_report)], 180, cwd=isolated, stage=report['stage'])
        test = json.loads(test_report.read_text(encoding='utf-8'))
        if not test.get('passed') or not test.get('frozen'):
            raise ValueError('Packaged application self-test failed')
        report['packaged_check'] = test
        report['stage'] = 'publish-file'
        target = output / filename
        temporary = target.with_suffix('.tmp')
        try:
            shutil.copyfile(executable, temporary)
            temporary.chmod(executable.stat().st_mode)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        digest = hashlib.sha256()
        with target.open('rb') as stream:
            for data in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(data)
        report.update(passed=True, stage='complete', returncode=0, mode='onefile', artifact=target.name,
                      sha256=digest.hexdigest(), size=target.stat().st_size)
        print(f'\nREADY: {target}', flush=True)
        return 0
    except Exception as exc:
        report['error'] = str(exc)
        report['returncode'] = getattr(exc, 'returncode', None)
        report['traceback'] = traceback.format_exc()
        print('BUILD FAILED: ' + str(exc), file=sys.stderr, flush=True)
        return 1
    finally:
        status.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    sys.exit(build())
