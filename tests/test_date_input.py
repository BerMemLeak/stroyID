"""Date change events must not commit partial years or rebuild focused inputs."""
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtQml import QJSEngine

ROOT = Path(__file__).resolve().parents[1]


class DateInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.js = QJSEngine()
        self.evaluate('''
          var record={start:'2026-04-11',end:'2026-04-30',date:'2026-04-11'};
          var renders=0,saves=0,messages=[];
          var handlers={},document={activeElement:null,
            addEventListener:(name,handler)=>handlers[name]=handler};
          var window={manualSavingMode:true};
          var getEnt=()=>record,guard=()=>true,entKey=()=>'',
            getPath=(o,f)=>o[f],setPath=(o,f,v)=>o[f]=v,
            touch=()=>{},logH=()=>{},entLabel=()=>'',
            save=()=>saves++,render=()=>renders++,refreshChrome=()=>{},
            toast=message=>messages.push(message);
          function field(name){return {type:'date',tagName:'INPUT',
            dataset:{ent:'act',id:'a1',f:name,rr:'1'},
            validity:{badInput:false},value:record[name]};}
          function change(t,value){t.value=value;handlers.change({target:t});}
          function leave(t){document.activeElement=null;handlers.focusout({target:t});}
        ''')
        source = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
        self.evaluate(source[source.index('function apply(t,fromInput)'):source.index('function fsRename(t)')])

    def evaluate(self, source):
        value = self.js.evaluate(source)
        self.assertFalse(value.isError(), value.toString())
        return value

    def check(self, expression):
        self.assertTrue(self.evaluate(expression).toBool(), expression)

    def test_partial_end_year_keeps_focus_until_full_date_is_committed(self):
        self.evaluate("var t=field('end');document.activeElement=t;")
        for year in ['0002', '0020', '0202', '2026']:
            self.evaluate(f"change(t,'{year}-04-29')")
            self.check("document.activeElement===t && record.end==='2026-04-30' && renders===0 && saves===0 && messages.length===0")
        self.evaluate('leave(t)')
        self.check("record.end==='2026-04-29' && saves===1 && renders===0")

    def test_start_date_and_unfocused_calendar_change(self):
        self.evaluate("var t=field('start');document.activeElement=t;change(t,'2026-04-12');leave(t)")
        self.check("record.start==='2026-04-12' && renders===0")
        self.evaluate("change(t,'2026-04-13')")
        self.check("record.start==='2026-04-13' && renders===0")

    def test_invalid_range_is_checked_after_leaving_field(self):
        self.evaluate("var t=field('end');document.activeElement=t;change(t,'2026-04-10')")
        self.check('messages.length===0')
        self.evaluate('leave(t)')
        self.check("record.end==='2026-04-30' && t.value===record.end && messages.length===1 && renders===0")

    def test_incomplete_date_does_not_erase_saved_date(self):
        self.evaluate("var t=field('date');t.value='';t.validity.badInput=true;leave(t)")
        self.check("record.date==='2026-04-11' && t.value===record.date && saves===0 && messages.length===1")

    def test_clearing_date_is_committed_on_blur(self):
        self.evaluate("var t=field('date');document.activeElement=t;change(t,'');leave(t)")
        self.check("record.date==='' && saves===1 && renders===0")

    def test_other_change_controls_still_render(self):
        self.evaluate("var t=field('enabled');t.type='checkbox';t.checked=true;handlers.change({target:t})")
        self.check('record.enabled===true && saves===1 && renders===1')


if __name__ == '__main__':
    unittest.main()
