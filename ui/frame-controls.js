// A linked drawing keeps its act context throughout preview and every export path.
function drawingContext(p, s, item, vol, owner = null) {
  const record = item.record;
  const executionId = vol?.executionId || record.executionId || item.owner?.executionId || s.executionId;
  const linked = s.acts.filter(a => (!executionId || a.executionId === executionId) &&
    (a.id === item.owner?.id || a.schemeLinks.some(l => l.id === item.id)));
  const a = owner || linked.find(a => a.id === record.frameActId) || item.owner || linked[0];
  const sp = vol?.sp || s.subprofiles[0], per = person(sp?.execId);
  const signer = key => {
    const id = key === 'developed' ? record.frameSigners?.developed : s.frameSigners?.[key];
    const selected = person(id);
    return selected ? shortFio(selected.fio || selected.fioShort || '') : '';
  };
  const cipher = record.frameCipher || s.cipher || p.cipher || '';
  const code = s.code || '';
  const designation = record.frameCipher || s.cipher || (cipher && code && !cipher.endsWith('-' + code) && cipher !== code ? cipher + '-' + code : cipher || code);
  const ids = a ? [...new Set([...a.schemeLinks.map(l => l.id), ...a.schemes.map(x => x.id)])] : [];
  const position = ids.indexOf(item.id);
  return {templateKey: record.frameTemplate?.fileKey || record.frameTemplateKey || '', values: {
    Шифр: designation, Объект: p.name || '', Здание: p.short || '',
    Название_Схемы: [record.num, record.name || item.name].filter(Boolean).join(' · '),
    Организация: org(per?.orgId)?.short || p.genContractor || '',
    Разработал: signer('developed'), Проверил: signer('checked'), Нормоконтроль: signer('controlled'),
    Дата: fmtD(a?.date || ''), Дата_Акта: fmtD(a?.date || ''),
    Номер_Приложения: String(record.appNo || (position >= 0 ? position + 1 : '')),
    Стадия: record.stage ?? s.stage ?? p.stage ?? '', АОСР: a?.num || '',
    Работы: a ? [a.works, a.workQty, a.workUnit].filter(Boolean).join(' · ') : '',
    Система: s.name || code, Выполнение: execution(p, executionId)?.name || ''
  }};
}

const FRAME_SIGNER_ROLES = [['checked', 'Проверил'], ['controlled', 'Нормоконтроль']];
function frameSignerControls(s, item = null) {
  const settings = item ? item.record.frameSigners : s.frameSigners;
  const roles = item ? [['developed', 'Разработал']] : FRAME_SIGNER_ROLES;
  const inherited = item ? FRAME_SIGNER_ROLES.map(([key,label]) => {
    const selected = person(s.frameSigners?.[key]);
    return `<p class="small">${label}: ${esc(selected ? shortFio(selected.fio || selected.fioShort || '') : 'Не выбран в настройках системы')}</p>`;
  }).join('') : '';
  return `<div class="card"><h3>${item ? 'Разработчик схемы' : 'Подписанты рамок системы'}</h3><p class="small mut">${item ? 'Выберите человека, который выполнил чертёж. Проверяющий и нормоконтроль берутся из настроек системы.' : 'Проверяющий и нормоконтроль применяются ко всем схемам системы. Разработчик выбирается отдельно в каждой схеме.'} Дата берётся из связанного АОСР; место для подписи остаётся пустым.</p><div class="g2">${roles.map(([key,label]) => `<label>${label}<select data-frame-signer="${key}" data-s="${s.id}" ${item ? `data-x="${item.id}"` : ''}><option value="" ${!settings?.[key] ? 'selected' : ''}>Выберите подписанта</option>${S.lib.people.map(p=>`<option value="${esc(p.id)}" ${settings?.[key]===p.id?'selected':''}>${esc(p.fio || p.fioShort)}</option>`).join('')}</select></label>`).join('')}</div>${inherited}${item ? `<a href="#/s/${s.id}/params" data-mb="-1">Настроить подписантов системы</a>` : ''}</div>`;
}
document.addEventListener('change', event => {
  const el = event.target;
  if (!el.dataset.frameSigner || !guard()) return;
  const s = getEnt('sys', el.dataset.s), record = el.dataset.x ? drawingRecord(s, el.dataset.x).record : s;
  record.frameSigners ||= {};
  if (el.value === '__inherit__') delete record.frameSigners[el.dataset.frameSigner];
  else record.frameSigners[el.dataset.frameSigner] = el.value;
  commit('Изменены подписанты рамки');
});
const frameSystemView = V.s;
V.s = r => {
  const box = document.createElement('div');
  box.innerHTML = frameSystemView(r);
  const s = getEnt('sys', r[1]);
  if (r[2] === 'params' && s) box.querySelector('.page')?.insertAdjacentHTML('beforeend', `<div class="card"><h3>Стадия документации</h3>${F('Стадия в рамке', 'sys', s.id, 'stage', s.stage ?? '')}</div>` + frameSignerControls(s));
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
    const missing = ['Разработал', 'Проверил', 'Нормоконтроль'].filter(key => !values[key]);
    if (missing.length) warnings.add(d.name + (values.АОСР ? ' (к ' + values.АОСР + ')' : '') + ': ' + missing.join(', '));
  }));
  return [...warnings];
}
function drawingWarnings(plan) {
 const warnings=new Set();
 for(const v of plan.volumes)for(const d of v.documents){
  if(d.type!=='Исполнительная схема'||!('sourceNumber' in d))continue;
  const missing=[];
  if(!d.sourceNumber?.trim())missing.push('номер схемы');
  const title=(d.sourceTitle||'').trim();
  if(!title||/^(?:новая )?исполнительная схема$/i.test(title))missing.push('полное название схемы');
  if(missing.length)warnings.add((d.name||'Схема')+': '+missing.join(', '));
 }
 return [...warnings];
}
function drawingRecord(s,id){return resourceList(s).find(x=>x.id===id);}
function drawingPanel(p,s,item){const r=item.record,acts=s.acts.filter(a=>a.schemes.some(x=>x.id===item.id)||a.schemeLinks.some(l=>l.id===item.id));return `<div class="card"><h3>Реквизиты схемы</h3><label>Шифр в штампе (пусто — из системы)<input data-frame-field="frameCipher" data-s="${s.id}" data-x="${item.id}" value="${esc(r.frameCipher || '')}"></label><label>Номер схемы<input data-frame-field="num" data-s="${s.id}" data-x="${item.id}" value="${esc(r.num || '')}"></label><label>Название схемы<input data-frame-field="name" data-s="${s.id}" data-x="${item.id}" value="${esc(r.name || item.name)}"></label><label>Стадия (пусто — из системы)<input data-frame-field="stage" data-s="${s.id}" data-x="${item.id}" value="${esc(r.stage ?? '')}"></label></div>`+frameSignerControls(s,item)+`<div class="card"><h3>Рамка исполнительной схемы</h3><p><b>${esc(item.name)}</b> · ${esc(r.file||'PDF не загружен')}</p><p class="small mut">ГОСТ Р 21.101-2026: форма 3, основная надпись 185 × 55 мм; поле подшивки 20 мм, остальные поля 5 мм. Формат и ориентация каждого листа берутся из исходного PDF. Исходный файл сохраняется.</p><label class="row"><input type="checkbox" data-a="drawingToggle" data-s="${s.id}" data-x="${item.id}" ${r.frameEnabled?'checked':''}> Добавлять рамку при сборке PDF</label><p class="small mut">Если рамка уже есть на чертеже, оставьте эту настройку выключенной. Рамка накладывается поверх исходного листа без проверки существующего оформления. Масштаб и положение чертежа сохраняются.</p><div class="row mt">${B('Сохранить HTML-шаблон ГОСТ','drawingTemplateSave')}${B('Подгрузить свой HTML-шаблон','drawingTemplatePick',`data-s="${s.id}" data-x="${item.id}"`)}${(r.frameTemplate?.fileKey||r.frameTemplateKey)?B('Вернуть шаблон ГОСТ','drawingTemplateReset',`data-s="${s.id}" data-x="${item.id}"`):''}</div><p class="small mut">${esc(r.frameTemplateName||'Встроенный шаблон ГОСТ')}. Теги: {{Объект}}, {{Шифр}}, {{Система}}, {{АОСР}}, {{Работы}}, {{Выполнение}}, {{Лист}}, {{Листов}}. Изменяйте текст и оформление SVG внутри HTML.</p><div class="row mt"><label>Лист <input id="drawing-page" type="number" min="1" max="${r.pages||1}" value="1" style="width:70px"></label><label>Связанный АОСР <select id="drawing-act" data-s="${s.id}" data-x="${item.id}"><option value="">Автоматически по выполнению</option>${acts.map(a=>`<option value="${a.id}" ${a.id===r.frameActId?'selected':''}>${esc(a.num)}</option>`).join('')}</select></label>${B('Показать настоящий лист','drawingPreview',`data-s="${s.id}" data-x="${item.id}"`,'pri')}</div><div id="drawing-result" class="mt"><p class="small mut">Нажмите «Показать настоящий лист», чтобы проверить рамку на загруженном чертеже.</p></div></div>`;}
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
document.addEventListener('change',event=>{if(event.target.id!=='drawing-act')return;const el=event.target;if(!guard())return;drawingRecord(getEnt('sys',el.dataset.s),el.dataset.x).record.frameActId=el.value;save();});

document.addEventListener('change', event => {
  const el = event.target;
  if (!el.dataset.frameField || !guard()) return;
  const r = drawingRecord(getEnt('sys', el.dataset.s), el.dataset.x).record;
  const value = el.value.trim();
  if (['stage','frameCipher'].includes(el.dataset.frameField) && !value) delete r[el.dataset.frameField];
  else r[el.dataset.frameField] = value;
  commit('Изменены реквизиты рамки');
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
