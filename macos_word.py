"""Microsoft Word for macOS automation. No UI scripting or global Word shutdown."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

# Pass paths as JSON data, never interpolate them into executable JavaScript.
WORD_MAC_SCRIPT = r'''
ObjC.import('Foundation');
function run(args) {
    const text = $.NSString.stringWithContentsOfFileEncodingError(
        $(args[0]), $.NSUTF8StringEncoding, null);
    if (!text) throw new Error('Cannot read Word job manifest');
    const jobs = JSON.parse(text.js);
    if (!Array.isArray(jobs)) throw new Error('Expected an array of Word jobs');
    const word = Application("com.microsoft.Word");
    word.launch();
    for (const job of jobs) {
        if (typeof job.source !== 'string' || typeof job.target !== 'string')
            throw new Error('Invalid Word job paths');
        let doc = null;
        try {
            word.open(Path(job.source));
            doc = word.activeDocument;
            doc.saveAs({fileName: job.target, fileFormat: 'format PDF'});
        } finally {
            // Only the generated document opened above belongs to this job.
            // Keep Word and the user's other documents running.
            if (doc !== null) doc.close({saving: 'no'});
        }
    }
    return 'OK';
}
'''


def word_application():
    candidates = [Path('/Applications/Microsoft Word.app'),
                  Path.home() / 'Applications/Microsoft Word.app']
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    try:
        result = subprocess.run(['/usr/bin/mdfind', "kMDItemCFBundleIdentifier == 'com.microsoft.Word'"],
                                capture_output=True, text=True, timeout=10, check=False)
        if result.returncode == 0:
            for name in result.stdout.splitlines():
                candidate = Path(name)
                if candidate.name == 'Microsoft Word.app' and candidate.is_dir():
                    return candidate
    except (OSError, subprocess.TimeoutExpired):
        pass
    raise ValueError('Microsoft Word для macOS не найден. Установите Word и откройте его один раз.')


def _wait(process, timeout):
    end = time.monotonic() + timeout
    try:
        while process.poll() is None:
            if time.monotonic() >= end:
                raise TimeoutError('Word не завершил преобразование. Проверьте открытые окна Word и повторите сборку.')
            from PySide6.QtCore import QCoreApplication, QEventLoop
            QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            time.sleep(.04)
    except BaseException:
        if process.poll() is None:
            process.kill()  # Terminate our osascript only, never the user's Word.
        process.wait()
        raise


def convert_docx_batch(jobs):
    if not jobs:
        return
    word_application()
    sources = [(Path(source).resolve(), Path(target).resolve()) for source, target in jobs]
    if len({target for _, target in sources}) != len(sources):
        raise ValueError('Повторяющиеся пути результатов Word')
    for source, target in sources:
        if not source.is_file() or source.suffix.lower() != '.docx' or source == target:
            raise ValueError('Неверный исходный Word-файл: ' + str(source))
    with tempfile.TemporaryDirectory(prefix='stroiid-word-mac-') as folder:
        folder = Path(folder)
        script = folder / 'export.js'
        script.write_text(WORD_MAC_SCRIPT, encoding='utf-8')
        staged = [folder / f'result-{i}.pdf' for i in range(len(sources))]
        manifest = folder / 'jobs.json'
        manifest.write_text(json.dumps([{'source': str(source), 'target': str(pdf)}
            for (source, _), pdf in zip(sources, staged)], ensure_ascii=False), encoding='utf-8')
        log = folder / 'output.log'
        try:
            with log.open('wb') as output:
                process = subprocess.Popen(['/usr/bin/osascript', '-l', 'JavaScript', str(script), str(manifest)],
                                           stdout=output, stderr=subprocess.STDOUT)
                _wait(process, max(180, 30 * len(sources)))
            if process.returncode:
                raise ValueError(log.read_text('utf-8', errors='replace')[-1800:])
            # A stale or partially produced PDF must not be mistaken for success.
            from pypdf import PdfReader
            for pdf in staged:
                if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-') or not len(PdfReader(pdf).pages):
                    raise ValueError('Word не создал корректный PDF документа')
        except Exception as exc:
            detail = log.read_text('utf-8', errors='replace') if log.exists() else ''
            logs = Path.home() / 'Library/Logs/StroyID'
            logs.mkdir(parents=True, exist_ok=True)
            path = logs / ('word-' + str(time.time_ns()) + '.txt')
            path.write_text(str(exc) + '\n' + detail, encoding='utf-8')
            hint = ('Разрешите управление Microsoft Word: Системные настройки → Конфиденциальность и безопасность '
                    '→ Автоматизация → СтройИД (или Terminal при запуске из исходников).\n') if '-1743' in detail or '-1743' in str(exc) else ''
            raise ValueError(hint + 'Не удалось преобразовать документ в Word для macOS.\n' + str(exc) + '\nЖурнал: ' + str(path)) from exc
        for pdf, (_, target) in zip(staged, sources):
            target.parent.mkdir(parents=True, exist_ok=True)
            handle, name = tempfile.mkstemp(prefix='.stroiid-word-', suffix='.pdf', dir=target.parent)
            os.close(handle)
            temporary = Path(name)
            try:
                shutil.copyfile(pdf, temporary)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
