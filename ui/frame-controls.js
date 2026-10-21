// A linked drawing keeps its act context throughout preview and every export path.
function drawingContext(p, s, item, vol, owner = null) {
  const record = item.record;
  const executionId = vol?.executionId || record.executionId || item.owner?.executionId || s.executionId;
  const linked = s.acts.filter(a => (!executionId || a.executionId === executionId) &&
    (a.id === item.owner?.id || a.schemeLinks.some(l => l.id === item.id)));
  const a = owner || linked.find(a => a.id === record.frameActId) || item.owner || linked[0];
  const sp = documentProfile(s, a, vol || {}), per = person(sp?.execId);
  const rows = frameSignerRows(s, item).map(row => {
    const selected = person(row.personId);
    return {role: row.role, name: selected ? shortFio(selected.fio || selected.fioShort || '') : ''};
  });
  const signer = role => rows.find(row => row.role === role)?.name || '';
  const cipher = record.frameCipher || s.cipher || p.cipher || '';
  const code = s.code || '';
  const designation = record.frameCipher || s.cipher || (cipher && code && !cipher.endsWith('-' + code) && cipher !== code ? cipher + '-' + code : cipher || code);
  // Use the same attachment list as the printed AOSR, including other documents.
  const position = a ? actAttachmentEntries(a, s).findIndex(x => x.schemeId === item.id) :
    resourceList(s).filter(x => x.kind !== 'act' && (x.record.fileKey || x.record.file) &&
      !s.acts.some(act => act.schemeLinks.some(l => l.id === x.id))).findIndex(x => x.id === item.id);
  const date = a?.date || (!a ? s.sectionDate : '') || '';
  const stampDate = /^\d{4}-\d{2}-\d{2}$/.test(date) ? '"' + date.slice(8) + '" ' + date.slice(5, 7) + '.' + date.slice(0, 4) + 'г.' : fmtD(date);
  const base=wordContext(p,{...(vol||{}),s,sp,executionId},a?'a'+a.id:'title');
  return {templateKey: record.frameTemplate?.fileKey || record.frameTemplateKey || '', signerRows: rows, captionEnabled: true, sheetPlaces: {...record.sheetPlaces}, values: {...base.values,
    'Схема.Шифр': designation, 'Объект.Наименование': p.name || '', 'Схема.Здание': p.name || '',
    'Схема.Номер': String(record.num || a?.num || code).trim(),
    'АОСР.Работы': String(a?.works || record.name || item.name || '').trim(),
    'АОСР.МестоРабот': a?.place || '',
    'Схема.Наименование': [record.num, record.name || item.name].filter(Boolean).join(' · '),
    'Комплект.Компания.Наименование': org(p.exportIssuer)?.full || org(p.exportIssuer)?.short || '',
    'Рамка.Разработал': signer('Разработал'), 'Рамка.Проверил': signer('Проверил'), 'Рамка.Нормоконтроль': signer('Н. контр.') || signer('Нормоконтроль'),
    'Схема.Дата': fmtD(date), 'АОСР.Дата': fmtD(date), 'Приложение.Дата': stampDate,
    'Приложение.Основание': a ? 'К акту №' : 'К разделу',
    'Приложение.Документ': a?.num || s.cipher || '',
    'Приложение.Номер': String(record.appNo || (position >= 0 ? position + 1 : '')),
    'Схема.Стадия': record.stage ?? s.stage ?? p.stage ?? '', 'АОСР.Номер': a?.num || '',
    'Схема.Работы': a ? [a.works, a.workQty, a.workUnit].filter(Boolean).join(' · ') : '',
    'Раздел.Наименование': s.name || code, 'Выполнение.Наименование': execution(p, executionId)?.name || ''
  }};
}

// The title block has six physical 5 mm rows below its revision header.
const FRAME_SIGNER_LIMIT = 6;
const FRAME_ROW_ROLES = ['Разработал', 'Проверил', 'Рук. проекта', 'Производ. работ', 'Строит. контроль', 'Н. контр.', 'Утвердил'];
function frameSignerRows(s, item = null) {
  if (Array.isArray(item?.record.frameRows)) return item.record.frameRows;
  const rows = Array.isArray(s.frameRows) ? s.frameRows : [
    {role: 'Разработал', personId: ''},
    {role: 'Проверил', personId: s.frameSigners?.checked || ''},
    ...(s.frameSigners && 'controlled' in s.frameSigners ? [{role: 'Н. контр.', personId: s.frameSigners.controlled || ''}] : [])
  ];
  // Preserve explicit developers of existing drawings, but ignore obsolete
  // per-drawing reviewer overrides, just as the previous editor did.
  if (item?.record.frameSigners && 'developed' in item.record.frameSigners)
    return rows.map(row => row.role === 'Разработал' ? {...row, personId: item.record.frameSigners.developed || ''} : row);
  return rows;
}
function frameSignerControls(s, item = null) {
  const rows = frameSignerRows(s, item), inherited = !!item && !Array.isArray(item.record.frameRows),
    legacy = inherited && item.record.frameSigners && 'developed' in item.record.frameSigners,
    attrs = `data-s="${esc(s.id)}"${item ? ` data-x="${esc(item.id)}"` : ''}`,
    disabled = inherited ? ' disabled' : '';
  return `<div class="card" data-frame-rows ${attrs}><h3>Строки штампа · ${rows.length} из ${FRAME_SIGNER_LIMIT}</h3>
    <p class="small mut">${inherited ? (legacy ? 'Строки системы с ранее выбранным разработчиком этой схемы.' : 'Используются строки системы.') : item ? 'Собственные строки этой схемы.' : 'Общий состав строк для схем системы.'} Дата берётся из АОСР или раздела; подписи остаются пустыми.</p>
    ${rows.length ? `<div class="tw"><table class="tbl"><thead><tr><th>Роль в штампе</th><th>Человек</th><th>Порядок</th></tr></thead><tbody>${rows.map((row,i) => `<tr>
      <td><input aria-label="Роль, строка ${i+1}" list="frame-row-roles" data-frame-row-field="role" data-row="${i}" ${attrs} value="${esc(row.role || '')}"${disabled}></td>
      <td><select aria-label="Человек, строка ${i+1}" data-frame-row-field="personId" data-row="${i}" ${attrs}${disabled}><option value="">Выберите человека</option>${row.personId && !person(row.personId) ? `<option value="${esc(row.personId)}" selected>Человек удалён — выберите другого</option>` : ''}${S.lib.people.map(p => `<option value="${esc(p.id)}" ${row.personId===p.id?'selected':''}>${esc(p.fio || p.fioShort)}</option>`).join('')}</select></td>
      <td><div class="row">${B('↑','frameRowMove',`${attrs} data-row="${i}" data-step="-1" title="Выше"${disabled}${i===0&&!inherited?' disabled':''}`,'sm')}${B('↓','frameRowMove',`${attrs} data-row="${i}" data-step="1" title="Ниже"${disabled}${i===rows.length-1&&!inherited?' disabled':''}`,'sm')}${B('Удалить','frameRowRemove',`${attrs} data-row="${i}"${disabled}`,'sm')}</div></td>
    </tr>`).join('')}</tbody></table></div>` : '<p class="small mut">Строки не заполнены; ячейки штампа останутся пустыми.</p>'}
    <datalist id="frame-row-roles">${FRAME_ROW_ROLES.map(role => `<option value="${esc(role)}">`).join('')}</datalist>
    <div class="row mt">${inherited ? B('Настроить для этой схемы','frameRowsOverride',attrs,'pri') : B('Добавить строку','frameRowAdd',attrs+(rows.length>=FRAME_SIGNER_LIMIT?' disabled':''),'sm')}${item && (!inherited || legacy) ? B('Использовать строки системы','frameRowsInherit',attrs,'sm') : ''}</div>
    <p class="small mut">Не более ${FRAME_SIGNER_LIMIT} строк. Роли можно писать вручную и повторять. Пустые строки сохраняются в рамке.</p></div>`;
}
function frameRowsTarget(d) {
  const s = getEnt('sys', d.s), item = d.x ? drawingRecord(s, d.x) : null;
  return {s, item, record: item ? item.record : s};
}
function saveFrameRows(d, el) {
  const {s, item} = frameRowsTarget(d);
  touch(s);save();
  const box = el?.closest('[data-frame-rows]');
  if (box) box.outerHTML = frameSignerControls(s, item);
}
A.frameRowsOverride = (d, el) => {
  if (!guard(entKey('sys',d.s))) return;
  const {s,item,record} = frameRowsTarget(d);
  record.frameRows = frameSignerRows(s,item).map(row => ({...row}));
  saveFrameRows(d,el);
};
A.frameRowsInherit = (d, el) => {
  if (!guard(entKey('sys',d.s))) return;
  const {record} = frameRowsTarget(d);
  delete record.frameRows;delete record.frameSigners;
  saveFrameRows(d,el);
};
function editFrameRows(d, el, edit) {
  if (!guard(entKey('sys',d.s))) return;
  const {s,item,record} = frameRowsTarget(d);
  if (item && !Array.isArray(record.frameRows)) return;
  const rows = frameSignerRows(s,item).map(row => ({...row}));
  if (edit(rows) === false) return;
  record.frameRows = rows;saveFrameRows(d,el);
}
A.frameRowAdd = (d,el) => editFrameRows(d,el,rows => {
  if (rows.length >= FRAME_SIGNER_LIMIT) {toast('В штампе доступны только '+FRAME_SIGNER_LIMIT+' строк');return false;}
  rows.push({role:'',personId:''});
});
A.frameRowRemove = (d,el) => editFrameRows(d,el,rows => {
  const i=Number(d.row);if(!Number.isInteger(i)||i<0||i>=rows.length)return false;rows.splice(i,1);
});
A.frameRowMove = (d,el) => editFrameRows(d,el,rows => {
  const i=Number(d.row),step=Number(d.step),j=i+step;
  if(!Number.isInteger(i)||![-1,1].includes(step)||i<0||i>=rows.length||j<0||j>=rows.length)return false;
  [rows[i],rows[j]]=[rows[j],rows[i]];
});
function updateFrameRow(el) {
  const key=el.dataset.frameRowField;
  if(!['role','personId'].includes(key)||!guard(entKey('sys',el.dataset.s)))return;
  const {s,item,record}=frameRowsTarget(el.dataset),i=Number(el.dataset.row);
  if(item&&!Array.isArray(record.frameRows))return;
  const rows=frameSignerRows(s,item).map(row=>({...row}));
  if(!Number.isInteger(i)||i<0||i>=rows.length)return;
  rows[i][key]=el.value;record.frameRows=rows;touch(s);save();
}
document.addEventListener('input',event=>{if(event.target.dataset.frameRowField==='role')updateFrameRow(event.target);});
document.addEventListener('change',event=>{if(event.target.dataset.frameRowField==='personId')updateFrameRow(event.target);});
const frameSystemView = V.s;
V.s = r => {
  const box = document.createElement('div');
  box.innerHTML = frameSystemView(r);
  const s = getEnt('sys', r[1]);
  if (r[2] === 'params' && s) box.querySelector('.page')?.insertAdjacentHTML('beforeend', `<div class="card"><h3>Стадия документации</h3>${F('Стадия в рамке', 'sys', s.id, 'stage', s.stage ?? '')}${F('Дата раздела', 'sys', s.id, 'sectionDate', s.sectionDate || '', {type:'date'})}</div>` + frameSignerControls(s));
  return box.innerHTML;
};

const drawingSourcesOriginal=pdfSources;
pdfSources=(p,v)=>{const map=drawingSourcesOriginal(p,v);p.systems.forEach(s=>resourceList(s).forEach(item=>{if(!item.record.frameEnabled)return;const id=item.kind==='system'?'ss'+s.id:item.kind==='extra'?'sk'+item.id:'c'+item.id;if(map.has(id))map.get(id).frame=drawingContext(p,s,item,v);}));return map;};
// Each framed drawing belongs to its act, even when its source is shared.
const drawingBlocksOriginal = blocksFor;
blocksFor = (p, v) => {
  const blocks = drawingBlocksOriginal(p, v), s = v.s;
  const block = blocks.find(b => b.key === 'schemes');
  if (!s || !block) return blocks;
  const acts = sortActs(s.acts.filter(a => a.type === 'АОСР' &&
    a.executionId === v.executionId && a.subs.includes(v.sp.id)));
  resourceList(s).filter(item => item.record.frameEnabled).forEach(item => {
    const fullId = item.kind === 'system' ? 'ss' + s.id : item.kind === 'extra' ? 'sk' + item.id : 'c' + item.id;
    const owners = acts.filter(a => a.id === item.owner?.id || a.schemeLinks.some(l => l.id === item.id));
    const replacement = [];
    owners.forEach(a => {
      const links = a.schemeLinks.filter(l => l.id === item.id);
      const ranges = a.id === item.owner?.id ? [{from: 1, to: item.record.pages}] : links;
      ranges.forEach((link, i) => replacement.push({
        id: 'framed:' + item.id + ':' + a.id + ':' + i,
        type: 'Исполнительная схема', name: item.record.name || item.name,
        nd: 'к ' + a.num + ', листы ' + link.from + '–' + link.to,
        pages: Number(link.to) - Number(link.from) + 1, file: item.record.file || '',
        ref: '#/a/' + a.id + '/schemes',
        pdf: {...pdfSource(item.record), from: Number(link.from), to: Number(link.to),
          frame: drawingContext(p, s, item, v, a)}
      }));
    });
    // Preserve unlinked full sources; replace shared ones by the act copies.
    if (!replacement.length) return;
    const index = block.items.findIndex(it => it.id === fullId || it.id.startsWith('linked:' + item.id + ':'));
    block.items = block.items.filter(it => it.id !== fullId && !it.id.startsWith('linked:' + item.id + ':'));
    block.items.splice(index < 0 ? block.items.length : index, 0, ...replacement);
  });
  const order = S.volCfg[p.id + '|' + v.key]?.docs?.schemes;
  if (order) block.items.sort((a, b) =>
    (order.includes(a.id) ? order.indexOf(a.id) : 1e6) -
    (order.includes(b.id) ? order.indexOf(b.id) : 1e6));
  const count = blocks.filter(b => !b.off && !b.auto).reduce((n, b) => n + b.items.length, 0);
  const reg = blocks.find(b => b.auto);
  if (reg) reg.items[0].pages = Math.max(1, Math.ceil((count + 1) / 22));
  return blocks;
};
function frameWarnings(plan) {
  const warnings = new Set();
  plan.volumes.forEach(v => v.documents.forEach(d => {
    if (!d.frame) return;
    const values = d.frame.values;
    const missing = Array.isArray(d.frame.signerRows) ? d.frame.signerRows.flatMap((row,i) => [
      ...(!row.role?.trim() ? ['роль в строке '+(i+1)] : []),
      ...(!row.name?.trim() ? [row.role?.trim() || 'человек в строке '+(i+1)] : [])
    ]) : ['Разработал', 'Проверил', 'Нормоконтроль'].filter(key => !values[key]);
    if (missing.length) warnings.add(d.name + (values['АОСР.Номер'] ? ' (к ' + values['АОСР.Номер'] + ')' : '') + ': ' + missing.join(', '));
  }));
  return [...warnings];
}
function drawingWarnings(plan) {
 const warnings=new Set();
 for(const v of plan.volumes)for(const d of v.documents){
  if(d.type!=='Исполнительная схема'||!('sourceNumber' in d))continue;
  const missing=[];
  // Validate the values actually printed, including automatic AOSR defaults.
  const number=String(d.frame?.values?.['Схема.Номер'] || d.sourceNumber || '').trim();
  if(!number)missing.push('номер схемы');
  const title=String(d.frame?.values?.['АОСР.Работы'] || d.sourceTitle || '').trim();
  if(!title||/^(?:новая )?исполнительная схема$/i.test(title))missing.push('полное название схемы');
  if(missing.length)warnings.add((d.name||'Схема')+': '+missing.join(', '));
 }
 return [...warnings];
}
function drawingRecord(s,id){return resourceList(s).find(x=>x.id===id);}

function drawingSheetCaption(config, page) {
  const values=config.values, base=String(values['Схема.Номер'] || '').trim(),
    number=base ? base+'.'+page : String(page),
    work=String(values['АОСР.Работы'] || '').trim(),
    place=String(config.sheetPlaces?.[String(page)] || '').trim(),
    text=[work,place].filter(Boolean).join(' ');
  return 'Исполнительная схема № '+number+(text ? ' «'+text+'»' : '');
}
function drawingSheetControls(p,s,item) {
  const count=Number(item.record.pages);
  if(!Number.isInteger(count)||count<1)return '';
  const config=drawingContext(p,s,item,null);
  return `<div class="card" data-sheet-places data-s="${esc(s.id)}" data-x="${esc(item.id)}"><h3>Место выполнения по листам PDF</h3>
    <p class="small mut">Надпись в центре каждого листа формируется автоматически из номера схемы, номера листа, работ АОСР и места этого листа. Если место не заполнено, оно не добавляется; общее место АОСР сюда не подставляется.</p>
    <div class="lst" style="max-height:420px;overflow:auto">${Array.from({length:count},(_,i)=>{const page=i+1;return `<div class="mb"><label class="fld"><span>Лист ${page} — место выполнения</span><textarea rows="2" data-sheet-place="${page}" data-s="${esc(s.id)}" data-x="${esc(item.id)}" placeholder="Например: на 3-м этаже в осях 3–21/Ж–Ф, отм. +7.000">${esc(item.record.sheetPlaces?.[String(page)] || '')}</textarea></label><p class="small mut" data-sheet-caption="${page}">${esc(drawingSheetCaption(config,page))}</p></div>`}).join('')}</div></div>`;
}
function refreshDrawingSheetCaptions(d) {
  const {p,o:s}=ctx('sys',d.s),item=drawingRecord(s,d.x);
  if(!item)return;
  const config=drawingContext(p,s,item,null);
  document.querySelectorAll('[data-sheet-places]').forEach(box=>{
    if(box.dataset.s!==d.s||box.dataset.x!==d.x)return;
    box.querySelectorAll('[data-sheet-caption]').forEach(el=>el.textContent=drawingSheetCaption(config,Number(el.dataset.sheetCaption)));
  });
}
document.addEventListener('input',event=>{
  const el=event.target;if(!el.dataset.sheetPlace||!guard(entKey('sys',el.dataset.s)))return;
  const {s,item,record}=frameRowsTarget(el.dataset),page=Number(el.dataset.sheetPlace);
  if(!item||!Number.isInteger(page)||page<1||page>Number(record.pages))return;
  record.sheetPlaces={...record.sheetPlaces};
  if(el.value.trim())record.sheetPlaces[String(page)]=el.value;
  else delete record.sheetPlaces[String(page)];
  touch(s);save();refreshDrawingSheetCaptions(el.dataset);
});

function drawingPanel(p,s,item){const r=item.record,acts=s.acts.filter(a=>a.schemes.some(x=>x.id===item.id)||a.schemeLinks.some(l=>l.id===item.id));return `<div class="card"><h3>Реквизиты схемы</h3><label>Шифр в штампе (пусто — из системы)<input data-frame-field="frameCipher" data-s="${s.id}" data-x="${item.id}" value="${esc(r.frameCipher || '')}"></label><label>Номер приложения (пусто — автоматически)<input type="number" min="1" step="1" data-frame-field="appNo" data-s="${s.id}" data-x="${item.id}" value="${esc(r.appNo || '')}" placeholder="Автоматически"></label><label>Номер схемы<input data-frame-field="num" data-s="${s.id}" data-x="${item.id}" value="${esc(r.num || '')}"></label><label>Название схемы<input data-frame-field="name" data-s="${s.id}" data-x="${item.id}" value="${esc(r.name || item.name)}"></label><label>Стадия (пусто — из системы)<input data-frame-field="stage" data-s="${s.id}" data-x="${item.id}" value="${esc(r.stage ?? '')}"></label></div>`+drawingSheetControls(p,s,item)+frameSignerControls(s,item)+`<div class="card"><h3>Рамка исполнительной схемы</h3><p><b>${esc(item.name)}</b> · ${esc(r.file||'PDF не загружен')}</p><p class="small mut">ГОСТ Р 21.101-2026: форма 3, основная надпись 185 × 55 мм; поле подшивки 20 мм, остальные поля 5 мм. Формат и ориентация каждого листа берутся из исходного PDF. Исходный файл сохраняется.</p><label class="row"><input type="checkbox" data-a="drawingToggle" data-s="${s.id}" data-x="${item.id}" ${r.frameEnabled?'checked':''}> Добавлять рамку и блок приложения при сборке PDF</label><p class="small mut">Если рамка уже есть на чертеже, оставьте эту настройку выключенной. Рамка накладывается поверх исходного листа без проверки существующего оформления. Масштаб и положение чертежа сохраняются.</p><div class="row mt">${B('Сохранить HTML-шаблон ГОСТ','drawingTemplateSave')}${B('Подгрузить свой HTML-шаблон','drawingTemplatePick',`data-s="${s.id}" data-x="${item.id}"`)}${(r.frameTemplate?.fileKey||r.frameTemplateKey)?B('Вернуть шаблон ГОСТ','drawingTemplateReset',`data-s="${s.id}" data-x="${item.id}"`):''}</div><p class="small mut">${esc(r.frameTemplateName||'Встроенный шаблон ГОСТ')}. Теги строк: {{Рамка.Строка1.Роль}}…{{Рамка.Строка6.Роль}}, {{Рамка.Строка1.ФамилияИнициалы}}…{{Рамка.Строка6.ФамилияИнициалы}}, {{Рамка.Строка1['Схема.Дата']}}…{{Рамка.Строка6['Схема.Дата']}}. Теги: {{Лист.Надпись}}, {{Лист.НомерСхемы}}, {{Лист.МестоРабот}}, {{АОСР.Работы}}, {{Объект.Наименование}}, {{Схема['Схема.Шифр']}}, {{Раздел.Наименование}}, {{АОСР.Номер}}, {{Схема.Работы}}, {{Выполнение.Наименование}}, {{Лист.Номер}}, {{Лист.Всего}}. Изменяйте текст и оформление SVG внутри HTML.</p><div class="row mt"><label>Лист <input id="drawing-page" type="number" min="1" max="${r.pages||1}" value="1" style="width:70px"></label><label>Связанный АОСР <select id="drawing-act" data-s="${s.id}" data-x="${item.id}"><option value="">Автоматически по выполнению</option>${acts.map(a=>`<option value="${a.id}" ${a.id===r.frameActId?'selected':''}>${esc(a.num)}</option>`).join('')}</select></label>${B('Показать настоящий лист','drawingPreview',`data-s="${s.id}" data-x="${item.id}"`,'pri')}</div><div id="drawing-result" class="mt"><p class="small mut">Нажмите «Показать настоящий лист», чтобы проверить рамку на загруженном чертеже.</p></div></div>`;}
A.drawingToggle=(d,el)=>{if(!guard()){el.checked=!el.checked;return;}drawingRecord(getEnt('sys',d.s),d.x).record.frameEnabled=el.checked;commit('Изменена рамка схемы');};
A.drawingEdit=d=>{const {p,o:s}=ctx('sys',d.s),item=drawingRecord(s,d.x);modal('Рамка и предпросмотр',drawingPanel(p,s,item),[{l:'Готово',c:'pri'}],'wide');};
A.drawingTemplateSave=async()=>{try{await nativeCall('saveFrameTemplate');}catch(e){toast(e.message);}};
A.drawingTemplatePick=async d=>{if(!guard())return;try{const f=await desktopTrack(nativeCall('pickFrameTemplate'));if(!f)return;Object.assign(drawingRecord(getEnt('sys',d.s),d.x).record,{frameTemplate:{fileKey:f.id,file:f.name,pages:0},frameTemplateName:f.name});commit('Загружен HTML-шаблон рамки');A.drawingEdit(d);}catch(e){toast(e.message);}};
A.drawingTemplateReset=d=>{if(!guard())return;const r=drawingRecord(getEnt('sys',d.s),d.x).record;delete r.frameTemplateKey;delete r.frameTemplate;delete r.frameTemplateName;commit('Возвращён шаблон ГОСТ');A.drawingEdit(d);};
A.drawingPreview=async d=>{const {p,o:s}=ctx('sys',d.s),item=drawingRecord(s,d.x),target=$('#drawing-result');if(!item.record.fileKey){toast('Загрузите PDF схемы');return;}const aid=$('#drawing-act')?.value,a=s.acts.find(a=>a.id===aid),e=execution(p,a?.executionId||item.record.executionId||S.ui.executionId)||p.executions[0],v=volumeList(p).find(v=>v.executionId===e?.id&&v.s?.id===s.id),page=Number($('#drawing-page')?.value||1);if(target)target.innerHTML='<p>Подготовка настоящего листа…</p>';try{await desktopFlush();const r=await desktopTrack(nativeCall('previewDrawing',{key:item.record.fileKey,page,frame:item.record.frameEnabled?drawingContext(p,s,item,v,a):null}));if(target?.isConnected)target.innerHTML=`<p class="small">${r.width} × ${r.height} мм · лист ${page} из ${r.pages}</p><img class="frame-preview" src="${r.image}" alt="Настоящий лист загруженной схемы с выбранной рамкой">`;}catch(e){if(target?.isConnected)target.innerHTML='<p>'+esc(e.message)+'</p>';}};
const drawingSchemeCatalog=schemeCatalog;schemeCatalog=(p,s)=>{const box=document.createElement('div');box.innerHTML=drawingSchemeCatalog(p,s);box.querySelectorAll('.resource').forEach((card,i)=>{const item=resourceList(s)[i];card.insertAdjacentHTML('beforeend',B('Рамка и предпросмотр','drawingEdit',`data-s="${s.id}" data-x="${item.id}"`,'sm'));});return box.innerHTML;};
schemeTab=(p,s)=>drawingPanel(p,s,drawingRecord(s,'system'))+`<div class="card">${B(s.scheme.file?'Заменить PDF':'Загрузить PDF','schemeFile',`data-s="${s.id}"`)}${s.scheme.fileKey?B('Открыть исходный PDF','openBlob',`data-key="${s.scheme.fileKey}"`):''}</div>`;
A.stampApply=d=>A.drawingEdit({...d,x:'system'});

A.ownPrev=d=>{const {s}=ctx('act',d.id);A.drawingEdit({s:s.id,x:d.x});};
document.addEventListener('change',event=>{if(event.target.id!=='drawing-act')return;const el=event.target;if(!guard())return;drawingRecord(getEnt('sys',el.dataset.s),el.dataset.x).record.frameActId=el.value;save();refreshDrawingSheetCaptions(el.dataset);});

document.addEventListener('change', event => {
  const el = event.target;
  if (!el.dataset.frameField || !guard()) return;
  const r = drawingRecord(getEnt('sys', el.dataset.s), el.dataset.x).record;
  const value = el.value.trim();
  if (el.dataset.frameField === 'appNo' && value && (!Number.isInteger(Number(value)) || Number(value) < 1)) { el.value = r.appNo || ''; toast('Введите целый положительный номер приложения'); return; }
  if (['stage','frameCipher','appNo'].includes(el.dataset.frameField) && !value) delete r[el.dataset.frameField];
  else r[el.dataset.frameField] = value;
  commit('Изменены реквизиты рамки');refreshDrawingSheetCaptions(el.dataset);
});

function confirmFrameWarnings(plans) {
  const warnings = [...new Set(plans.flatMap(plan=>[...frameWarnings(plan),...drawingWarnings(plan)]))];
  if (!warnings.length) return Promise.resolve(true);
  return new Promise(resolve => {
    const root = $('#modal-root');
    const done = value => { observer.disconnect(); resolve(value); };
    const observer = new MutationObserver(() => {
      if (!root.querySelector('[data-frame-warning]')) done(false);
    });
    modal('Проверьте реквизиты схем', `<div data-frame-warning><p>Не заполнены следующие поля:</p><div style="white-space:pre-wrap">${esc(warnings.join('\n'))}</div></div>`, [
      {l: 'Вернуться', f: () => done(false)},
      {l: 'Продолжить с пустыми ячейками', c: 'pri', f: () => done(true)}
    ]);
    observer.observe(root, {childList: true, subtree: true});
  });
}
