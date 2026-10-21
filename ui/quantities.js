/* Work quantities are optional per AOSR; their template and rows are reusable. */
const QUANTITY_SECTION=['quantity','Ведомость объёмов работ','Ведомости объёмов выполненных работ','Документы инженерных систем'];
WORD_SECTIONS.splice(WORD_SECTIONS.findIndex(x=>x[0]==='aosr')+1,0,QUANTITY_SECTION);
function quantityEnabled(a){return a.type==='АОСР'&&a.quantityEnabled!==false;}
function quantityRows(a){return Array.isArray(a.quantityRows)?a.quantityRows:[{id:'initial',name:a.works||'',place:a.place||'',unit:a.workUnit||'',qty:a.workQty??''}];}
const quantityEnsure=ensureWorkspace;
ensureWorkspace=()=>{quantityEnsure();if(!S)return;S.projects.forEach(p=>p.systems.forEach(s=>s.acts.forEach(a=>{if(a.type==='АОСР'&&!Array.isArray(a.quantityRows))a.quantityRows=quantityRows(a);})));};
function quantityIssues(a){
 const rows=quantityRows(a),issues=[];
 if(!rows.length)issues.push('добавьте хотя бы одну строку объёмов');
 rows.forEach((r,i)=>{
  if(!(r.name||a.works||'').trim())issues.push('строка '+(i+1)+': укажите работу');
  if(!(r.unit||'').trim())issues.push('строка '+(i+1)+': укажите единицу измерения');
  const qty=String(r.qty??'').trim().replace(/\s/g,'').replace(',','.');
  if(!/^\d+(?:\.\d+)?$/.test(qty)||!Number.isFinite(Number(qty)))issues.push('строка '+(i+1)+': введите неотрицательное число в количестве');
 });return issues;
}
function quantityName(a){return 'Ведомость объёмов выполненных работ к '+a.type+' № '+a.num;}
function quantityMarker(a){return '[[QUANTITY_SHEETS:'+a.id+']]';}
const quantityEntries=actAttachmentEntries;
actAttachmentEntries=(a,s)=>{
 const entries=quantityEntries(a,s);
 if(quantityEnabled(a)){let pos=entries.findIndex(x=>!x.name.startsWith('Исполнительная схема'));if(pos<0)pos=entries.length;entries.splice(pos,0,{name:quantityName(a),pages:1,quantityId:a.id});}
 return entries;
};
function quantityAttachmentText(a,s,actual=false){return actAttachmentEntries(a,s).map((x,i)=>(i+1)+'. '+x.name+', '+(actual&&x.quantityId?quantityMarker(a):x.pages||'?')+' л.').join('\n')||'Не выбраны';}
function quantitySource(p,s,a,v){
 const issues=quantityIssues(a);
 if(issues.length)return {kind:'missing',error:'Ведомость к '+a.num+': '+issues.join('; ')};
 const t=wordChoice(p,v,'quantity');
 if(t&&!t.fileKey)return {kind:'missing',error:'Загрузите выбранный шаблон ведомости «'+t.name+'»'};
 try{return {kind:'word',...(t?{templateKey:t.fileKey,templateName:t.name}:{builtinTemplate:'quantity'}),...validateDocumentContext(wordContext(p,v,'quantity:'+a.id),t?.tags||['Объект.Наименование','АОСР.Номер'])};}catch(e){return {kind:'missing',error:e.message};}
}
const quantityBlocks=blocksFor;
blocksFor=(p,v)=>{
 const blocks=quantityBlocks(p,v);
 for(const block of blocks){
  const items=[];
  for(const item of block.items){items.push(item);const a=v.s?.acts.find(a=>item.id==='a'+a.id);
   if(a&&quantityEnabled(a))items.push({id:'quantity:'+a.id,type:'Ведомость объёмов работ',name:quantityName(a),nd:'к '+a.num,pages:1,file:'Ведомость_'+a.num+'.docx',ref:'#/a/'+a.id+'/quantity'});
  }block.items=items;
 }
 const count=blocks.filter(b=>!b.off&&!b.auto).reduce((sum,b)=>sum+b.items.length,0),reg=blocks.find(b=>b.auto);
 if(reg)reg.items[0].pages=Math.max(1,Math.ceil((count+1)/22));
 return blocks;
};
const quantitySources=pdfSources;
pdfSources=(p,v)=>{
 const sources=quantitySources(p,v);
 for(const s of p.systems)for(const a of s.acts){
  if(!quantityEnabled(a))continue;
  sources.set('quantity:'+a.id,quantitySource(p,s,a,v));
  const source=sources.get('a'+a.id);
  if(!source||source.kind==='pdf'||source.kind==='missing')continue;
  const marker=quantityMarker(a),estimate=quantityAttachmentText(a,s),actual=quantityAttachmentText(a,s,true);
  if(source.values)source.values={...source.values,'АОСР.Приложения':actual};
  if(source.html)source.html=source.html.replaceAll(esc(estimate).replace(/\n/g,'<br>'),esc(actual).replace(/\n/g,'<br>')).replaceAll(esc(estimate),esc(actual));
  source.attachmentPageRefs={[marker]:'quantity:'+a.id};
 }
 return sources;
};
// Explicit attachment selection may omit the quantity sheet for this export only.
const quantityPlans=assemblyPlans;
assemblyPlans=(p,c)=>{
 const plans=quantityPlans(p,c);
 for(const {plan} of plans)for(const v of plan.volumes){const ids=new Set(v.documents.map(d=>d.id));
  for(const doc of v.documents){
   if(!doc.attachmentPageRefs||Object.values(doc.attachmentPageRefs).every(id=>ids.has(id)))continue;
   const pair=p.systems.flatMap(s=>s.acts.map(a=>({s,a}))).find(x=>doc.id==='a'+x.a.id);
   if(!pair)continue;
   const {s,a}=pair,copy={...a,quantityEnabled:false};
   if(doc.values)doc.values={...doc.values,'АОСР.Приложения':appsText(copy,s)};
   if(doc.html){const sp=spOf(s,a.subs[0])||s.subprofiles[0];doc.html=aosrHtml(copy,p,s,sp);}
   delete doc.attachmentPageRefs;
  }
 }
 return plans;
};
function quantityPanel(a){
 const on=quantityEnabled(a),rows=quantityRows(a);
 return `<div class="card"><h3>Ведомость объёмов выполненных работ</h3><label class="row"><input type="checkbox" data-quantity-toggle="${a.id}" ${on?'checked':''}>Включать ведомость в комплект этого АОСР</label><p class="small mut">Каждая строка — отдельный объём. Файл формируется из Word-шаблона и располагается сразу после АОСР. Расчёты и вычеты автоматически не выполняются.</p>${on?`<div style="overflow-x:auto"><table class="tbl"><thead><tr><th>№</th><th>Работа / участок</th><th>Место выполнения</th><th>Ед. изм.</th><th>Количество</th><th></th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td>${[['name','Например: монтаж лотка'],['place','Оси, этаж, отметка'],['unit','м, м², шт.'],['qty','0,00']].map(([key,hint])=>`<td><input aria-label="${hint}, строка ${i+1}" data-quantity-act="${a.id}" data-quantity-row="${r.id}" data-quantity-field="${key}" value="${esc(String(r[key]??''))}" placeholder="${esc(hint)}" ${key==='qty'?'inputmode="decimal"':''} style="min-width:${['name','place'].includes(key)?'180':'80'}px"></td>`).join('')}<td>${B('Удалить','quantityRemove',`data-id="${a.id}" data-row="${r.id}"`,'sm')}</td></tr>`).join('')}</tbody></table></div><div class="row mt">${B('Добавить строку','quantityAdd',`data-id="${a.id}"`,'pri')}${B('Скачать ведомость DOCX','quantityDownload',`data-id="${a.id}"`)}</div><label class="fld mt"><span>Пояснение (необязательно)</span><textarea data-quantity-note="${a.id}">${esc(a.quantityNote||'')}</textarea></label><p class="small">Составил — представитель лица, выполнившего работы. Проверил — представитель строительного контроля лица, осуществляющего строительство.</p>`:''}</div>`;
}
const quantityActView=V.a;
V.a=r=>{const html=quantityActView(r),a=getEnt('act',r[1]);if(!a||a.type!=='АОСР')return html;const box=document.createElement('div');box.innerHTML=html;const tabs=box.querySelector('.tabs');if(tabs)tabs.insertAdjacentHTML('beforeend',`<a href="#/a/${a.id}/quantity" class="tab ${r[2]==='quantity'?'on':''}">Объёмы работ</a>`);if(r[2]==='quantity')box.querySelector('.page')?.insertAdjacentHTML('beforeend',quantityPanel(a));else if(!r[2]||r[2]==='main')box.querySelector('.page')?.insertAdjacentHTML('beforeend',`<div class="card"><h3>Объёмы работ</h3><p>${quantityEnabled(a)?'Ведомость включена · строк: '+quantityRows(a).length:'Ведомость выключена'}</p><a href="#/a/${a.id}/quantity">Заполнить ведомость объёмов</a></div>`);return box.innerHTML;};
A.quantityAdd=d=>{if(!guard())return;const a=getEnt('act',d.id);a.quantityRows=quantityRows(a);a.quantityRows.push({id:uid(),name:'',place:'',unit:'',qty:''});commit('Добавлена строка ведомости',a);};
A.quantityRemove=d=>{if(!guard())return;const a=getEnt('act',d.id);a.quantityRows=quantityRows(a).filter(r=>r.id!==d.row);commit('Удалена строка ведомости',a);};
document.addEventListener('input',event=>{const el=event.target;if(!el.dataset.quantityField&&!el.dataset.quantityNote)return;if(!guard())return;const a=getEnt('act',el.dataset.quantityAct||el.dataset.quantityNote);if(el.dataset.quantityNote)a.quantityNote=el.value;else {a.quantityRows=quantityRows(a);const row=a.quantityRows.find(r=>r.id===el.dataset.quantityRow);if(row)row[el.dataset.quantityField]=el.value;}save();});
document.addEventListener('change',event=>{const id=event.target.dataset.quantityToggle;if(!id||!guard())return;const a=getEnt('act',id);a.quantityEnabled=event.target.checked;commit('Изменено включение ведомости',a);});
A.quantityDownload=async d=>{try{const {p,s,o:a}=ctx('act',d.id),v=volumeList(p).find(v=>v.s?.id===s.id&&v.sp.id===a.subs[0]);if(!v)throw Error('Назначьте акту комплект подписантов');const source=quantitySource(p,s,a,v);if(source.kind==='missing')throw Error(source.error);await desktopFlush();const result=await desktopTrack(nativeCall('saveGeneratedDocx',{...source,filename:'Ведомость_'+a.num+'.docx'}));if(result)toast('Ведомость сохранена');}catch(e){toast(e.message);}};
const quantityPreview=A.wordPreview;
A.wordPreview=async d=>{const t=tpl(d.id);if(!t||wordKey(t)!=='quantity')return quantityPreview(d);try{const {p}=wordUIContext(),v=volumeList(p).find(v=>v.s?.acts.some(a=>a.type==='АОСР')),a=v?.s.acts.find(a=>a.type==='АОСР');if(!a)throw Error('Создайте АОСР для предпросмотра ведомости');await desktopTrack(nativeCall('openFilledWord',{key:t.fileKey,...validateDocumentContext(wordContext(p,v,'quantity:'+a.id),t?.tags||[])}));}catch(e){toast(e.message);}};
