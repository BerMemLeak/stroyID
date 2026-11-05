"""Build and verify a single executable containing Python, Qt and the UI."""
import argparse
import hashlib
import json
import platform
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
import time
from datetime import datetime, timezone
from pathlib import Path

# All child Python processes must read the repository's Cyrillic JSON as UTF-8.
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.9.5'


def command(args, timeout=900, cwd=ROOT, stage='command', logs=None):
    logs = Path(logs) if logs is not None else ROOT / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    log_path = logs / (stage + '.log')
    printable = subprocess.list2cmdline([str(x) for x in args])
    print('\nSTAGE: ' + stage + '\n> ' + printable + '\nLOG: ' + str(log_path), flush=True)
    started = time.monotonic()
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
            print('\n'.join(lines[-400:]), flush=True)
        print(f'TIME: {stage}: {time.monotonic() - started:.1f} s', flush=True)


def close_running_release(target):
    """Request a normal UI close only for processes running this exact EXE."""
    if sys.platform != 'win32':
        return
    script = ROOT / 'tools' / 'close_release.ps1'
    subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                    '-File', str(script), '-Executable', str(target.resolve())],
                   timeout=25, check=True)


def publish_executable(executable, target):
    """Replace the fixed release path after a normal close and bounded retries."""
    descriptor, name = tempfile.mkstemp(prefix=target.stem + '-', suffix='.tmp', dir=target.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copyfile(executable, temporary)
        temporary.chmod(executable.stat().st_mode)
        for attempt in range(11):
            try:
                temporary.replace(target)
                return target
            except PermissionError as error:
                if attempt == 0:
                    print('Закрытие запущенной версии перед заменой ' + str(target), flush=True)
                    close_running_release(target)
                if attempt == 10:
                    raise PermissionError('Не удалось заменить ' + str(target) +
                        '. Закройте СтройИД и проверьте доступ к файлу; новая сборка сохранена в ' + str(executable)) from error
                time.sleep(0.5)
    finally:
        temporary.unlink(missing_ok=True)


def build(*, quick=False):
    output = ROOT / 'release'
    output.mkdir(exist_ok=True)
    report = {'version': VERSION, 'platform': sys.platform, 'python': sys.version,
              'created': datetime.now(timezone.utc).isoformat(), 'passed': False, 'error': None,
              'stage': 'initialization', 'returncode': None, 'quick': quick}
    status = output / 'build-report.json'
    try:
        report['platform'] = platform.platform()
        is_mac = sys.platform == 'darwin'
        if is_mac:
            from macos_release import require_native_mac
            require_native_mac()
        command([sys.executable, 'tools/build_frontend.py'], stage='frontend')
        report['stage'] = 'unit-tests'
        command([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 120, stage=report['stage'])
        smoke_checks = [
            ('qt-word-templates', 'smoke_word.py', 120),
            ('qt-manual-save-and-idle', 'smoke_manual.py', 150),
        ] if quick else [
            ('document-tags', 'smoke_document_tags.py', 120),
            ('qt-interface', 'smoke_qt.py', 120),
            ('qt-pdf-export', 'smoke_pdf.py', 120),
            ('qt-word-templates', 'smoke_word.py', 120),
            ('qt-aosr-quantities', 'smoke_quantities.py', 150),
            ('qt-print-materials', 'smoke_print_materials.py', 150),
            ('qt-folder-workspace', 'smoke_folders.py', 120),
            ('qt-organization-role-picker', 'smoke_org_roles.py', 120),
            ('qt-executions-and-frames', 'smoke_executions.py', 120),
            ('qt-act-attachment-bundles', 'smoke_act_bundles.py', 120),
            ('qt-manual-save-and-idle', 'smoke_manual.py', 150),
            ('qt-local-regressions', 'smoke_regressions.py', 150),
            ('qt-save-locks', 'smoke_save_locks.py', 150),
            ('qt-document-workflow', 'smoke_workflow.py', 120),
            ('qt-snapshot', 'smoke_snapshot.py', 150),
            ('qt-frame-reference', 'smoke_frames.py', 120),
            ('qt-navigation-and-preview', 'smoke_navigation.py', 120),
        ]
        for stage, script, timeout in smoke_checks:
            report['stage'] = stage
            command([sys.executable, 'tests/' + script], timeout, stage=stage)
        if is_mac:
            report['stage'] = 'macos-word-integration'
            command([sys.executable, 'tests/smoke_word_macos.py', str(output/'word-macos-check.json')],
                    240, stage=report['stage'])
            report['word_integration'] = json.loads((output/'word-macos-check.json').read_text('utf-8'))
            report['stage'] = 'macos-icon'
            command([sys.executable, 'tools/macos_release.py', 'icon'], 90, stage=report['stage'])
        report['stage'] = 'pyinstaller'
        clean = [] if quick else ['--clean']
        command([sys.executable, '-m', 'PyInstaller', '--noconfirm', *clean,
                 '--distpath', 'dist-macos' if is_mac else 'dist-onefile',
                 'StroyID-macos.spec' if is_mac else 'StroyID.spec'], stage=report['stage'])
        filename = 'StroyID.exe' if sys.platform == 'win32' else 'StroyID'
        bundle = ROOT/'dist-macos/StroyID.app' if is_mac else None
        executable = bundle/'Contents/MacOS/StroyID' if is_mac else ROOT/'dist-onefile'/filename
        if is_mac:
            from macos_release import validate_bundle
            report['stage'] = 'macos-bundle-validation'
            report['bundle'] = validate_bundle(bundle)
        test_report = output / 'packaged-self-test.json'
        test_report.unlink(missing_ok=True)
        # Prove that the executable runs after copying it alone into an otherwise empty folder.
        with tempfile.TemporaryDirectory(prefix='stroiid-onefile-proof-') as isolated:
            isolated = Path(isolated)
            if is_mac:
                copied_bundle = isolated/'StroyID.app'
                shutil.copytree(bundle, copied_bundle, symlinks=True)
                copied = copied_bundle/'Contents/MacOS/StroyID'
            else:
                copied = isolated / filename
                shutil.copy2(executable, copied)
            report['stage'] = 'onefile-self-test'
            command([str(copied), '--self-test', str(test_report)], 180, cwd=isolated, stage=report['stage'])
        test = json.loads(test_report.read_text(encoding='utf-8'))
        if not test.get('passed') or not test.get('frozen'):
            raise ValueError('Packaged application self-test failed')
        report['packaged_check'] = test
        if is_mac:
            target = bundle
        else:
            report['stage'] = 'publish-file'
            target = publish_executable(executable, output / filename)
        digest = hashlib.sha256()
        hash_file = executable if is_mac else target
        with hash_file.open('rb') as stream:
            for data in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(data)
        report.update(passed=True, stage='complete', returncode=0, mode='macos-app' if is_mac else 'onefile', artifact=target.name,
                      artifact_path=str(target.relative_to(ROOT)),
                      sha256=digest.hexdigest(), sha256_file=str(hash_file.relative_to(target)) if is_mac else target.name,
                      size=sum(p.stat().st_size for p in target.rglob('*') if p.is_file() and not p.is_symlink()) if is_mac else target.stat().st_size)
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
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true', help='Run the local Windows check set')
    args = parser.parse_args()
    if args.quick and sys.platform != 'win32':
        parser.error('--quick is for Windows builds')
    sys.exit(build(quick=args.quick))
