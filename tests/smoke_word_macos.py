"""Optional real-Word integration on the user's Mac; CI records absence explicitly."""
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stroyid.infrastructure.documents.word_templates import sample_docx, inspect_docx, fill_docx, convert_docx_batch
from pypdf import PdfReader


def run(report_path):
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'status': 'skipped', 'reason': 'Microsoft Word for macOS is unavailable'}
    try:
        if sys.platform != 'darwin':
            return 0
        if os.environ.get('STROYID_SKIP_WORD_INTEGRATION') == '1':
            report['reason']='Real Word integration explicitly disabled on this unattended runner'
            return 0
        from stroyid.infrastructure.documents.macos_word import word_application
        try:
            word_application()
        except ValueError as exc:
            report['reason'] = str(exc)
            return 0
        with tempfile.TemporaryDirectory(prefix='СтройИД проверка Word ') as temp:
            root = Path(temp)
            template = sample_docx('title', 'Проверка Word для macOS', root/'template.docx')
            values = {tag: 'Проверка' for tag in inspect_docx(template.read_bytes())['tags']}
            jobs=[]
            for i in range(2):
                source = root/f'акт «тест» {i}.docx'
                fill_docx(template.read_bytes(), source, values)
                jobs.append((source, root/f'результат {i}.pdf'))
            convert_docx_batch(jobs)
            for _, target in jobs:
                reader=PdfReader(target)
                assert len(reader.pages)>0
                assert 'проверка' in ''.join(p.extract_text() or '' for p in reader.pages).lower()
            report={'status':'passed','documents':len(jobs),'engine':'Microsoft Word for macOS'}
        return 0
    except Exception as exc:
        report={'status':'failed','error':str(exc)}
        raise
    finally:
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    sys.exit(run(sys.argv[1] if len(sys.argv)>1 else 'release/word-macos-check.json'))
