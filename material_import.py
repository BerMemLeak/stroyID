"""Strict one-material-per-row XLSX import with relative, verified PDF sources."""
from copy import deepcopy
from datetime import date, datetime
import hashlib
import re
import uuid
from pathlib import Path
from pypdf import PdfReader

BASE_HEADERS = ['Код материала', 'Наименование материала', 'Марка']
DOC_FIELDS = ['тип', 'номер', 'дата', 'файл']


def headers(groups=5):
    return BASE_HEADERS + [f'Документ {i}: {field}' for i in range(1,groups+1) for field in DOC_FIELDS]


def text(value):
    return str(value).strip() if value is not None else ''


def parse_date(value):
    if value in (None, ''):return ''
    if isinstance(value, (datetime,date)):return value.date().isoformat() if isinstance(value,datetime) else value.isoformat()
    for fmt in ('%d.%m.%Y','%Y-%m-%d'):
        try:return datetime.strptime(text(value),fmt).date().isoformat()
        except ValueError:pass
    raise ValueError('дата должна иметь формат ДД.ММ.ГГГГ')


def pdf_source(root, relative):
    relative=text(relative).replace('\\','/')
    if not relative or Path(relative).is_absolute() or re.match(r'^[A-Za-z]:',relative):
        raise ValueError('укажите относительный путь к PDF внутри выбранной папки')
    path=(root/relative).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower()!='.pdf':
        raise ValueError('PDF не найден внутри выбранной папки: '+relative)
    raw=path.read_bytes()
    try:
        import io
        pdf=PdfReader(io.BytesIO(raw))
        if pdf.is_encrypted or not len(pdf.pages):raise ValueError('пустой или защищённый PDF')
        pages=len(pdf.pages)
    except Exception as exc:raise ValueError('нечитаемый PDF: '+relative) from exc
    return {'path':str(path),'relative':relative,'hash':hashlib.sha256(raw).hexdigest(),'pages':pages}


def preview_import(xlsx, folder, state):
    from openpyxl import load_workbook
    root=Path(folder).resolve();errors=[];items=[];codes=set();names=set()
    book=load_workbook(xlsx,read_only=True,data_only=False)
    try:
        if book.sheetnames!=['Материалы']:raise ValueError('Ожидается один лист «Материалы». Скачайте шаблон в приложении.')
        rows=book['Материалы'].iter_rows();first=next(rows,[]);cols=[text(c.value) for c in first]
        while cols and not cols[-1]:cols.pop()
        groups=(len(cols)-3)//4
        if groups<1 or cols!=headers(groups):raise ValueError('Неверные заголовки. Используйте шаблон и полные группы столбцов «Документ N».')
        for rn,row in enumerate(rows,2):
            if any(text(c.value) for c in row[len(cols):]):
                errors.append(f'Строка {rn}: данные за пределами известных столбцов');continue
            vals=[c.value for c in row[:len(cols)]]
            if not any(v is not None and text(v) for v in vals):continue
            if any(c.data_type=='f' for c in row):errors.append(f'Строка {rn}: формулы не допускаются');continue
            vals += [None]*(len(cols)-len(vals));code,name,brand=map(text,vals[:3])
            if not name:errors.append(f'Строка {rn}: не заполнено наименование материала')
            if code and code.casefold() in codes:errors.append(f'Строка {rn}: повтор кода {code}')
            identity=(name.casefold(),brand.casefold())
            if identity in names:errors.append(f'Строка {rn}: материал с такой маркой уже есть в Excel')
            names.add(identity)
            if code:codes.add(code.casefold())
            docs=[];hashes=set()
            for i in range(groups):
                kind,num,dt,file=vals[3+i*4:7+i*4]
                if not any(text(v) for v in (kind,num,dt,file)):continue
                try:
                    if not text(kind) or not text(file):raise ValueError('обязательны тип документа и файл')
                    date_value=parse_date(dt);source=pdf_source(root,file)
                    if source['hash'] in hashes:raise ValueError('этот файл уже указан у материала')
                    hashes.add(source['hash']);docs.append({'type':text(kind),'num':text(num),'date':date_value,**source})
                except ValueError as exc:errors.append(f'Строка {rn}, документ {i+1}: {exc}')
            if not docs:errors.append(f'Строка {rn}: не добавлены документы качества')
            matches=[m for m in state['lib']['base'] if (code and m.get('importCode','').casefold()==code.casefold()) or
                (m.get('name','').strip().casefold(),m.get('brand','').strip().casefold())==identity]
            items.append({'row':rn,'code':code,'name':name,'brand':brand,'docs':docs,
                'matches':[{'id':m['id'],'name':m['name'],'brand':m.get('brand','')} for m in matches]})
    finally:book.close()
    if not items and not errors:errors.append('В Excel нет материалов для импорта')
    return {'items':items,'errors':errors,'root':str(root)}


def commit_import(store, preview, choices):
    loaded=store.load()
    if store.heads != preview.get('heads', store.heads) or loaded['conflicts'] or loaded['warnings']:
        raise ValueError('База изменилась или содержит ошибки. Повторите проверку импорта.')
    if preview['errors']:raise ValueError('Исправьте все ошибки Excel перед импортом')
    state=deepcopy(loaded['state']);base=state['lib']['base'];prepared=[]
    for item in preview['items']:
        selected=choices.get(str(item['row']))
        if selected is None or selected not in ['new',*[m['id'] for m in item['matches']]]:
            raise ValueError(f"Строка {item['row']}: выберите существующий материал или создание нового")
        for doc in item['docs']:
            actual=pdf_source(Path(preview['root']),doc['relative'])
            if actual['hash']!=doc['hash']:raise ValueError('Файл изменился после проверки: '+doc['relative'])
        prepared.append((item,selected))
    added=0;skipped=0
    for item,selected in prepared:
        material=next((m for m in base if m['id']==selected),None)
        if material is None:
            material={'id':'b'+uuid.uuid4().hex,'name':item['name'],'brand':item['brand'],
                'importCode':item['code'],'category':'','maker':'','note':'','docs':[],'scope':'common'}
            base.append(material)
        docs=material.setdefault('docs',[])
        existing=docs+[q for q in state['lib'].get('quality',[]) if q['id'] in material.get('docIds',[])]
        hashes={d.get('fileHash') for d in existing if d.get('fileHash')}
        for d in existing:
            if d.get('fileKey') and not d.get('fileHash'):
                path,_=store.asset_path(d['fileKey']);hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
        for doc in item['docs']:
            if doc['hash'] in hashes:skipped+=1;continue
            file=store.import_file(doc['path'])
            if file['sha256']!=doc['hash']:raise ValueError('Файл изменился во время импорта: '+doc['relative'])
            docs.append({'id':'q'+uuid.uuid4().hex,'type':doc['type'],'num':doc['num'],'date':doc['date'],
                'pages':doc['pages'],'file':file['name'],'fileKey':file['id'],'fileHash':file['sha256']})
            hashes.add(doc['hash']);added+=1
    from folder_core import validate_state
    validate_state(state)
    result=store.save(state,loaded['revision'])
    result.update(importedMaterials=len(prepared),importedDocuments=added,skippedDocuments=skipped)
    return result
