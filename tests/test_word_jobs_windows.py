"""Exercise the actual Windows PowerShell JSON loop with a fake Word COM object."""
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from word_templates import WORD_SCRIPT

@unittest.skipUnless(shutil.which('powershell.exe'), 'Windows PowerShell is required')
class WordJobsWindowsTests(unittest.TestCase):
 def test_multiple_unicode_sources_are_opened_individually(self):
  with tempfile.TemporaryDirectory(prefix='СтройИД Word ') as tmp:
   root=Path(tmp);jobs=[]
   for i in range(3):
    source=root/f'исходник {i}.docx';source.write_text(f'document-{i}',encoding='utf-8')
    jobs.append({'source':str(source),'target':str(root/f'результат {i}.pdf')})
   manifest=root/'jobs.json';manifest.write_text(json.dumps(jobs,ensure_ascii=False),encoding='utf-8-sig')
   fake=r'''& {
     $documents=New-Object PSObject
     $documents | Add-Member ScriptMethod Open { param($path,$confirm,$readOnly,$recent)
       if (!(Test-Path -LiteralPath $path)) { throw ('Invalid single source: '+$path) }
       $doc=New-Object PSObject -Property @{ Source=$path }
       $doc | Add-Member ScriptMethod Repaginate { }
       $doc | Add-Member ScriptMethod Close { param($save) }
       $doc | Add-Member ScriptMethod ExportAsFixedFormat { param($target,$format)
         [IO.File]::WriteAllText($target,[IO.File]::ReadAllText($this.Source))
       }
       return $doc
     }
     $word=New-Object PSObject -Property @{ Documents=$documents; Visible=$false; DisplayAlerts=0; AutomationSecurity=0 }
     $word | Add-Member ScriptMethod Quit { param($save) }
     return $word
   }'''
   script=root/'export.ps1';script.write_text(WORD_SCRIPT.replace('New-Object -ComObject Word.Application',fake),encoding='utf-8-sig')
   result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),str(manifest)],capture_output=True,timeout=30)
   self.assertEqual(result.returncode,0,result.stderr.decode('utf-8','replace'))
   for i,job in enumerate(jobs):self.assertEqual(Path(job['target']).read_text(encoding='utf-8'),f'document-{i}')
if __name__=='__main__':unittest.main()
