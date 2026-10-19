/* PDF assembly for the desktop application. Sources are resolved by managed IDs. */
function pdfSource(record){return {kind:'pdf',key:record?.fileKey||'',declaredFile:record?.file||'',sourceRecordId:record?.id||'',sourceNumber:record?.num||'',sourceTitle:record?.name||''};}
function pdfTitle(p,vol){return `<p align="center">${esc(p.developer||'')}</p><p align="center">${esc(p.techCustomer||'')}</p><br><br><h1>ИСПОЛНИТЕЛЬНАЯ<br>ДОКУМЕНТАЦИЯ</h1><br><p align="center"><b>${esc(p.name)}</b></p><p align="center">${esc(p.address)}</p><br><h2>${esc(vol.title)}</h2><p align="center">Шифр: ${esc(vol.s?.cipher||p.cipher||'')}</p><br><br><p align="center">${esc(p.genContractor||'')}</p><p align="center">${new Date().getFullYear()}</p>`;}
function pdfJournal(j){return `<h2>${esc(j.name)}</h2><table border="1" cellspacing="0" cellpadding="4" width="100%"><thead><tr><th>№</th>${j.cols.map(c=>'<th>'+esc(c)+'</th>').join('')}</tr></thead><tbody>${j.rows.map((r,i)=>'<tr><td>'+(i+1)+'</td>'+j.cols.map((_,k)=>'<td>'+esc(r.c[k]||'')+'</td>').join('')+'</tr>').join('')}</tbody></table>`;}
function pdfPhotos(a){
 const per=[1,2,4].includes(Number(a.photoLayout))?Number(a.photoLayout):2,parts=[];
 for(let i=0;i<a.photos.length;i+=per){const photos=a.photos.slice(i,i+per);
  if(photos.some(p=>!p.img))return {kind:'missing',error:'не загружены фотографии; откройте вкладку «Фото»'};
  const cols=per===4?2:1,rows=[];
  for(let k=0;k<photos.length;k+=cols)rows.push('<tr>'+photos.slice(k,k+cols).map(p=>`<td align="center"><img src="${esc(p.img)}" width="${per===4?260:540}" height="${per===1?700:per===4?250:320}"><p>${esc(p.cap)}</p></td>`).join('')+'</tr>');
  parts.push(`<h2>Фототаблица к ${esc(a.num)}</h2><table width="100%" cellspacing="0" cellpadding="5">${rows.join('')}</table><p align="center">Лист ${parts.length+1} из ${Math.ceil(a.photos.length/per)}</p>`);
 }
 return {kind:'html',parts};
}
function pdfSources(p,vol){
 const sources=new Map(),put=(id,source)=>sources.set(id,source);
 put('title',{kind:'html',html:pdfTitle(p,vol)});put('reg',{kind:'registry'});
 p.admin.forEach(x=>put('admin'+x.id,pdfSource(x)));
 p.surveys.forEach(x=>put('v'+x.id,pdfSource(x)));
 p.opsDocs.forEach(x=>put('op'+x.id,pdfSource(x)));
 p.journals.forEach(j=>put('j'+j.id,j.mode==='B'?pdfSource(j):{kind:'html',html:pdfJournal(j),landscape:true}));
 p.materials.forEach(m=>mDocs(m).forEach(d=>put('q'+d.id,pdfSource(d))));
 p.systems.forEach(s=>{
  put('ss'+s.id,pdfSource(s.scheme));s.sketches.forEach(x=>put('sk'+x.id,pdfSource(x)));
  s.trials.forEach(x=>put('trial'+x.id,pdfSource(x)));
  s.journals.forEach(j=>put('j'+j.id,j.mode==='B'?pdfSource(j):{kind:'html',html:pdfJournal(j),landscape:true}));
  s.aik.forEach(k=>{const m=pMat(p,k.materialId);put('k'+k.id,k.file||k.fileKey?pdfSource(k):{kind:'html',html:`<h2>АКТ № ${esc(k.num)}</h2><p align="center"><b>входного контроля материалов и изделий</b></p><p>Объект: ${esc(p.name)}</p><p>Система: ${esc(s.code)}. Дата: ${fmtD(k.date)}</p><p>Материал: ${esc(mName(m))}</p><p>Количество: ${esc(k.qty||'')}</p><p>Документы качества: ${mDocs(m).map(x=>esc(x.type+' № '+x.num+' от '+fmtD(x.date))).join('; ')}</p><p>Примечание: ${esc(k.note||'')}</p><p>Заключение комиссии: ____________________________________</p><p>Подписи: ____________________________________</p><p class="small">Форма сформирована из карточки. Проверьте содержание и подписи перед передачей.</p>`});});
  s.acts.forEach(a=>{
   const sp=vol.s?.id===s.id?vol.sp:spOf(s,a.subs[0])||s.subprofiles[0]||{name:'',signers:{}};
   const invalidLink=linkedSchemes(a,s).some(({link,item})=>!item||!Number.isInteger(Number(link.from))||!Number.isInteger(Number(link.to))||Number(link.from)<1||Number(link.to)<Number(link.from)||Number(link.to)>Number(item.record.pages))||a.testLinks.some(id=>!s.trials.some(t=>t.id===id));
   put('a'+a.id,invalidLink?{kind:'missing',error:'исправьте связи со схемами или испытаниями'}:a.scan?.file||a.scan?.fileKey?pdfSource(a.scan):{kind:'html',html:aosrHtml(a,p,s,sp)+'<p class="small">Форма сформирована из карточки. Проверьте содержание и подписи перед передачей.</p>'});
   put('p'+a.id,pdfPhotos(a));a.schemes.forEach(x=>put('c'+x.id,pdfSource(x)));
   a.tests.forEach(x=>put('t'+x.id,pdfSource(x)));
   a.materials.map(id=>pMat(p,id)).filter(Boolean).forEach(m=>mDocs(m).forEach(d=>put('q'+d.id+'_'+a.id,pdfSource(d))));
  });
 });return sources;
}
// Add selected sheets when their complete source is not already present in the schemes section.
const pdfPreviousBlocks=blocksFor;
blocksFor=(p,vol)=>{
 const blocks=pdfPreviousBlocks(p,vol),b=blocks.find(b=>b.key==='schemes');
 if(b&&vol.s){const s=vol.s,seen=new Set(b.items.map(x=>x.id));
  sortActs(s.acts.filter(a=>a.type==='АОСР'&&a.subs.includes(vol.sp.id))).forEach(a=>linkedSchemes(a,s).forEach(({link,item})=>{
   const fullId=item?.kind==='system'?'ss'+s.id:item?.kind==='extra'?'sk'+item.id:'c'+item?.id;
   if(item&&seen.has(fullId))return;
   const id='linked:'+link.id+':'+link.from+':'+link.to;if(seen.has(id))return;seen.add(id);
   b.items.push({id,type:'Исполнительная схема',name:item?.name||'Источник схемы удалён',nd:'к '+a.num+', листы '+link.from+'-'+link.to,pages:Number(link.to)-Number(link.from)+1,file:item?.record.file||'',ref:'#/a/'+a.id+'/schemes',pdf: {...pdfSource(item?.record),from:Number(link.from),to:Number(link.to)}});
  }));
  const order=S.volCfg[p.id+'|'+vol.key]?.docs?.schemes;if(order)b.items.sort((x,y)=>(order.includes(x.id)?order.indexOf(x.id):1e6)-(order.includes(y.id)?order.indexOf(y.id):1e6));
 }
 const count=blocks.filter(b=>!b.off&&!b.auto).reduce((n,b)=>n+b.items.length,0),reg=blocks.find(b=>b.auto);if(reg)reg.items[0].pages=Math.max(1,Math.ceil((count+1)/22));
 return blocks;
};
function exportSourceOrigin(p,vol,block,item,source){
 let ref=item.ref||'',cardKey='',section=block.title,extra='';
 const match=(record,prefix)=>record&&(item.id===prefix+record.id||source.sourceRecordId===record.id);
 for(const [field,prefix,tab,label] of [['admin','admin','admin','Организационные документы'],['surveys','v','survey','Исполнительные съёмки'],['opsDocs','op','ops','Эксплуатационные документы'],['journals','j','ozhr','Журналы объекта']]){
  const record=p[field].find(x=>match(x,prefix));if(record){ref='#/p/'+p.id+'/'+tab;cardKey=field+':'+record.id;section=label;}
 }
 for(const material of p.materials){const record=mDocs(material).find(x=>match(x,'q')||item.id.startsWith('q'+x.id+'_'));if(record){ref='#/m/'+material.id;cardKey=(material.baseId?'base:'+material.baseId:'materials:'+material.id);section='Документы качества';extra=mName(material);}}
 for(const system of p.systems){
  for(const [field,prefix,tab] of [['sketches','sk','schemes'],['trials','trial','trials'],['journals','j','jr'],['aik','k','aik']]){const record=system[field].find(x=>match(x,prefix));if(record){ref='#/s/'+system.id+'/'+tab;cardKey=field+':'+record.id;extra=system.code;}}
  if(item.id==='ss'+system.id){ref='#/s/'+system.id+'/schemes';cardKey='systems:'+system.id;extra=system.code;}
  for(const act of system.acts){const tab=item.id==='a'+act.id?'main':item.id==='p'+act.id?'photos':act.schemes.some(x=>match(x,'c'))?'schemes':act.tests.some(x=>match(x,'t'))?'tests':'';if(tab){ref='#/a/'+act.id+'/'+tab;cardKey='acts:'+act.id;extra=system.code+' · '+act.num;}}
 }
 return {sourceRef:ref||('#/p/'+p.id+'/general'),cardKey,sourceLocation:[p.short||p.name,vol.execution?.name,extra||vol.s?.code,section,item.name].filter(Boolean).join(' → ')};
}
function pdfPlan(p,volumes){return {object:p.name,volumes:volumes.map(vol=>{const sources=pdfSources(p,vol);return {title:vol.title,documents:blocksFor(p,vol).filter(b=>!b.off).flatMap(b=>b.items.map(it=>{const source=it.pdf||sources.get(it.id)||{kind:'missing',error:'нет доступного источника'};return {id:it.id,type:it.type,name:it.name,nd:it.nd,...source,...exportSourceOrigin(p,vol,b,it,source)};}))};})};}

let pdfExportBusy=false;
A.downloadAssemblyPdf=async d=>{
 if(pdfExportBusy)return;const {p,vol}=curVol(),all=d?.all==='1',volumes=all?volumeList(p):[vol];
 pdfExportBusy=true;modal('Сборка PDF','<p>Подготовка документов и проверка исходных PDF…</p><p class="small mut">После проверки выберите, куда сохранить файл.</p>',[]);
 try{
  await new Promise(resolve=>setTimeout(resolve,80));await desktopFlush();
  const snapshot=pdfPlan(p,volumes);
  if(!await confirmFrameWarnings([snapshot])) return null;
  const r=await desktopTrack(nativeCall('exportPdf',{plan:snapshot,filename:slug(p.short||p.name)+'_'+(all?'Вся_ИД':slug(vol.short))+'.pdf'}));
  if(!r){closeModal();toast('Сохранение PDF отменено');return null;}
  S.builds=S.builds||[];S.builds.unshift({id:uid(),pid:p.id,key:all?'ALL':vol.key,ts:nowStr(),pages:r.pages,docs:r.documents,by:APP.user,format:'pdf'});
  logH('Собран PDF: '+(all?'вся ИД объекта':vol.short));save();await desktopFlush();
  modal('Комплект PDF сохранён',`<p><b>${r.pages} страниц · ${r.documents} документов</b></p><p>${esc(r.path)}</p><p class="small mut">В реестре указаны фактические страницы итогового PDF. Внутри есть закладки для томов и документов.</p>`,[{l:'Готово',c:'pri'}]);render();return r;
 }catch(e){modal('PDF не собран',`<p>Исправьте указанные источники и повторите сборку.</p><div style="white-space:pre-wrap;max-height:380px;overflow:auto">${esc(e.message)}</div>`,[{l:'Закрыть'}],'wide');return null;}
 finally{pdfExportBusy=false;}
};
const pdfPreviousBuild=V.build;
V.build=r=>pdfPreviousBuild(r).replace('HTML-прототип готовит реестр и состав тома. Склейка PDF, извлечение выбранных листов и наложение штампов на реальные PDF в этой версии не выполняются.','Скачайте один PDF выбранного тома или всей ИД объекта. Реестр пересчитывается по фактическим страницам. Загруженные PDF сохраняют формат листов; схемы включаются в исходном виде.').replace('Число страниц исходников задаётся вручную. Страницы форм актов и реестра в прототипе расчётные.','Здесь показана оценка страниц. При выгрузке PDF реестр пересчитывается по готовым документам; номера страниц сквозные, PDF сохраняется одним файлом.').replace('Подготовить комплект','Собрать и скачать PDF');
A.buildRun=()=>{const {p,vol}=curVol(),C=check(p),R=registry(p,vol);modal('Сборка комплекта ИД',`<div class="alert ${C.E.length||C.W.length?'al-a':'al-g'}">Замечаний по карточкам объекта: ${C.E.length+C.W.length}. Наличие и читаемость выбранных исходников проверяются при сборке PDF.</div><div class="kv"><div>Объект</div><div>${esc(p.short||p.name)}</div><div>Том</div><div>${esc(vol.title)}</div><div>Документы тома</div><div>${R.rows.filter(x=>!x.book).length}</div></div><div class="row mt">${B('Скачать PDF тома','downloadAssemblyPdf','','pri')}${B('Скачать всю ИД объекта','downloadAssemblyPdf','data-all="1"','pri')}</div><div class="row mt">${B('Скачать реестр CSV','regCsv')}${B('Скачать состав JSON','assemblyJson')}</div><div class="small mut mt">Титульные листы и реестры формируются автоматически. Подписанный скан акта используется вместо формы из карточки. Отсутствующие источники не пропускаются. Разделы, выключенные в составе каждого тома, не включаются.</div>`,[{l:'Закрыть'},{l:'Проверка карточек',f:()=>go('#/p/'+p.id+'/check')}],'wide');};
