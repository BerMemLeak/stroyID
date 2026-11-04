"""Mac Word jobs must preserve existing output on failure and safely pass paths."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from pypdf import PdfWriter
import macos_word as mac
import word_templates


def pdf_bytes():
    writer=PdfWriter();writer.add_blank_page(595,842);out=io.BytesIO();writer.write(out);return out.getvalue()


class MacWordTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='СтройИД Mac ')
        self.root=Path(self.tmp.name)
        self.jobs=[]
        for i in range(2):
            src=self.root/f'акт «{i}» \'quoted.docx';src.write_bytes(b'source')
            dst=self.root/f'готовый {i}.pdf';dst.write_bytes(b'old-result')
            self.jobs.append((src,dst))
        self.addCleanup(self.tmp.cleanup)

    def launch(self, output=None, error=None):
        def popen(args, **kwargs):
            self.assertEqual(args[:3],['/usr/bin/osascript','-l','JavaScript'])
            script=Path(args[3]).read_text('utf-8')
            jobs=json.loads(Path(args[4]).read_text('utf-8'))
            self.assertEqual([j['source'] for j in jobs],[str(s) for s,_ in self.jobs])
            for source,_ in self.jobs:self.assertNotIn(source.name,script)
            if error:
                kwargs['stdout'].write(error.encode())
            else:
                for job in jobs:Path(job['target']).write_bytes(output)
            return Mock(returncode=1 if error else 0, poll=lambda:1 if error else 0)
        return popen

    def test_batch_unicode_paths_are_data_and_outputs_are_validated(self):
        data=pdf_bytes()
        with patch.object(mac,'word_application'),patch.object(mac.subprocess,'Popen',side_effect=self.launch(data)):
            mac.convert_docx_batch(self.jobs)
        self.assertTrue(all(dst.read_bytes()==data for _,dst in self.jobs))
        self.assertTrue(all(src.read_bytes()==b'source' for src,_ in self.jobs))

    def test_permission_denial_preserves_outputs_and_provides_actionable_log(self):
        with patch.object(mac,'word_application'),patch.object(mac.Path,'home',return_value=self.root), \
             patch.object(mac.subprocess,'Popen',side_effect=self.launch(error='Not authorized (-1743)')):
            with self.assertRaisesRegex(ValueError,'Автоматизация'):mac.convert_docx_batch(self.jobs)
        self.assertTrue(all(dst.read_bytes()==b'old-result' for _,dst in self.jobs))
        logs=list((self.root/'Library/Logs/StroyID').glob('*.txt'))
        self.assertEqual(len(logs),1);self.assertIn('-1743',logs[0].read_text('utf-8'))

    def test_bad_pdf_does_not_replace_existing_result(self):
        with patch.object(mac,'word_application'),patch.object(mac.Path,'home',return_value=self.root), \
             patch.object(mac.subprocess,'Popen',side_effect=self.launch(output=b'not PDF')):
            with self.assertRaisesRegex(ValueError,'корректный PDF'):mac.convert_docx_batch(self.jobs)
        self.assertTrue(all(dst.read_bytes()==b'old-result' for _,dst in self.jobs))

    def test_timeout_reaps_only_the_automation_process(self):
        process=Mock();process.poll.return_value=None
        with patch.object(mac.time,'monotonic',side_effect=[0,999]):
            with self.assertRaises(TimeoutError):mac._wait(process,10)
        process.kill.assert_called_once();process.wait.assert_called_once()

    def test_platform_dispatch_and_word_open(self):
        with patch.object(word_templates.sys,'platform','darwin'),patch.object(mac,'convert_docx_batch') as convert:
            word_templates.convert_docx_batch(self.jobs);convert.assert_called_once_with(self.jobs)
        with patch.object(word_templates.sys,'platform','darwin'),patch.object(mac,'word_application',return_value=Path('/Applications/Microsoft Word.app')), \
             patch.object(word_templates.subprocess,'Popen') as run:
            word_templates.open_in_word(self.jobs[0][0])
        self.assertEqual(run.call_args.args[0],['/usr/bin/open','-a','/Applications/Microsoft Word.app',str(self.jobs[0][0])])


@unittest.skipUnless(sys.platform=='darwin','JXA interpreter requires macOS')
class MacNativeJxaTests(unittest.TestCase):
    def test_real_jxa_interpreter_reads_batch_and_exports_unicode_paths(self):
        # Run the production script with an in-memory Word double. This verifies
        # the native JXA/ObjC API without requiring Office or privacy permission in CI.
        with tempfile.TemporaryDirectory(prefix='СтройИД JXA ') as folder:
            root=Path(folder);jobs=[];data=pdf_bytes()
            for i in range(3):
                src=root/f'акт «{i}» \'source.docx';src.write_bytes(data)
                jobs.append({'source':str(src),'target':str(root/f'PDF {i}.pdf')})
            fake=r'''
ObjC.import('Foundation');
let current=null;
const fakeWord={
 launch:function(){},
 open:function(path){
  const source=path.toString();
  current={saveAs:function(options){
    if(options.fileFormat!=='format PDF')throw new Error('Wrong Word format');
    const bytes=$.NSData.dataWithContentsOfFile($(source));
    if(!bytes.writeToFileAtomically($(options.fileName),true))throw new Error('Cannot write PDF');
   },close:function(options){if(options.saving!=='no')throw new Error('Source must not be saved');}};
 },
 get activeDocument(){return current;}
};
'''
            script=root/'native.js'
            script.write_text(fake+mac.WORD_MAC_SCRIPT.replace('const word = Application("com.microsoft.Word");','const word = fakeWord;'),encoding='utf-8')
            manifest=root/'jobs.json';manifest.write_text(json.dumps(jobs,ensure_ascii=False),encoding='utf-8')
            result=subprocess.run(['/usr/bin/osascript','-l','JavaScript',str(script),str(manifest)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            for job in jobs:self.assertEqual(Path(job['target']).read_bytes(),data)


if __name__=='__main__':unittest.main()
