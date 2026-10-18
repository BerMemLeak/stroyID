"""One/many PDFs and actual-page registries without extra runtime dependencies."""
import csv,io,re,tempfile,zipfile,html,os
from pathlib import Path
from pdf_export import prepare_export,write_export

def registry_rows(prepared):
 rows=[]
 for volume in prepared['volumes']:
  for doc in volume['documents']:
   rows.append([volume['title'],doc.get('type',''),doc.get('name',''),doc.get('nd',''),doc.get('start',0),doc.get('end',0)])
 return rows

def write_registry(prepared,target,fmt):
 rows=[['Том / комплект','Тип документа','Наименование','Номер и дата','Лист с','Лист по'],*registry_rows(prepared)]
 target=Path(target)
 if fmt=='csv':
  stream=io.StringIO();csv.writer(stream,delimiter=';',lineterminator='\r\n').writerows(rows);target.write_bytes(stream.getvalue().encode('utf-8-sig'));return
 def col(n):return chr(65+n)
 cells=[]
 for ri,row in enumerate(rows,1):
  cs=[]
  for ci,v in enumerate(row):
   ref=col(ci)+str(ri)
   if isinstance(v,(int,float)):cs.append(f'<c r="{ref}"><v>{v}</v></c>')
   else:cs.append(f'<c r="{ref}" t="inlineStr"'+(' s="1"' if ri==1 else '')+f'><is><t xml:space="preserve">{html.escape(str(v))}</t></is></c>')
  cells.append(f'<row r="{ri}">'+''.join(cs)+'</row>')
 xmlhead='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml',xmlhead+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
  z.writestr('_rels/.rels',xmlhead+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
  z.writestr('xl/workbook.xml',xmlhead+'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Реестр ИД" sheetId="1" r:id="rId1"/></sheets></workbook>')
  z.writestr('xl/_rels/workbook.xml.rels',xmlhead+'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
  z.writestr('xl/styles.xml',xmlhead+'<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="2"><xf fontId="0"/><xf fontId="1" applyFont="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
  z.writestr('xl/worksheets/sheet1.xml',xmlhead+f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:F{len(rows)}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="2" width="28" customWidth="1"/><col min="3" max="3" width="65" customWidth="1"/><col min="4" max="4" width="28" customWidth="1"/><col min="5" max="6" width="12" customWidth="1"/></cols><sheetData>'+''.join(cells)+f'</sheetData><autoFilter ref="A1:F{len(rows)}"/></worksheet>')

def prepare_many(store,plans):
 if not plans:raise ValueError('Не выбраны документы')
 return [prepare_export(store,x['plan']) for x in plans]

def write_many(store,plans,prepared,target):
 target=Path(target).resolve()
 if target.is_relative_to(store.root):raise ValueError('Сохраните ZIP вне рабочей папки базы')
 with tempfile.TemporaryDirectory(prefix='sid-pdf-pack-') as temp:
  names=set();outputs=[]
  for i,(entry,ready) in enumerate(zip(plans,prepared),1):
   name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',entry.get('name') or 'Комплект')[:140]+'.pdf'
   if name in names:name=Path(name).stem+'_'+str(i)+'.pdf'
   names.add(name);file=Path(temp)/name;write_export(ready,file,store);outputs.append(file)
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
   for file in outputs:z.write(file,file.name)
 return {'path':str(target),'files':len(outputs),'pages':sum(x['pages'] for x in prepared),'documents':sum(x['documents'] for x in prepared)}
