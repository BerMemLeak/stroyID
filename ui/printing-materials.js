/* Materials import and print packets share the normal persisted cards and export plan. */
const ACT_REGISTERS=[['materials','материалов','М'],['evidence','подтверждающих документов','Д'],['attachments','приложений','П']];
WORD_SECTIONS.push(['actRegister','Реестр к АОСР','Реестры материалов, документов и приложений','Документы инженерных систем']);
function registerMetadata(p,volume,doc){
 const pair=p.systems.flatMap(s=>s.acts.map(a=>({s,a}))).find(x=>doc.id==='a'+x.a.id&&x.a.type==='АОСР');
 if(!pair)return;
 const {s,a}=pair,scope=volume.s?.id===s.id?volume:null,
  v={...volume,...scope,s,sp:scope?.sp||spOf(s,a.subs[0])||s.subprofiles[0],executionId:a.executionId};
 const context=wordContext(p,v,'a'+a.id),values={...(doc.actRegister?.values||context.values),...doc.values};
 if(doc.attachmentPageRefs&&!doc.values)values['АОСР.Приложения']=quantityAttachmentText(a,s,true);
 const lines=value=>String(value||'').split('\n').map(x=>x.trim().replace(/^\d+\.\s*/, '')).filter(Boolean);
 const materials=a.materials.map(id=>pMat(p,id)).filter(Boolean).map(m=>[mName(m),mDocs(m).map(d=>[d.type,d.num?'№ '+d.num:'',d.date?'от '+fmtD(d.date):''].filter(Boolean).join(' ')).join('; ')].filter(Boolean).join(' — '));
 const template=wordChoice(p,v,'actRegister');if(template&&!template.fileKey)throw Error('Загрузите выбранный Word-шаблон реестров к АОСР');
 const settings=structuredClone(a.registers||{});for(const r of Object.values(settings))if(r.date)r.date=fmtD(r.date);
 doc.actRegister={actId:a.id,number:a.num,settings,values,
  entries:{materials:[...materials,...lines(a.materialsNote)],evidence:lines(values['АОСР.ПодтверждающиеДокументы']),attachments:lines(values['АОСР.Приложения'])},
  signers:DOCUMENT_ROLES.map((role,i)=>[DOC_ROLES[i],values['Подписанты.'+role+'.ФамилияИнициалы']||'']),
  templateKey:doc.actRegister?.templateKey??template?.fileKey??'',builtinTemplate:'act-register'};
}
function decorateActPlan(p,plan){const scopes=volumeList(p);for(const v of plan.volumes){const scope=scopes.find(x=>x.key===v.key);for(const doc of v.documents)registerMetadata(p,{...v,...scope},doc);}return plan;}
const printPdfPlan=pdfPlan;pdfPlan=(p,volumes)=>decorateActPlan(p,printPdfPlan(p,volumes));
const printAssemblyPlans=assemblyPlans;assemblyPlans=(p,c)=>printAssemblyPlans(p,c).map(entry=>({...entry,plan:decorateActPlan(p,entry.plan)}));
const registerSample=A.wordSample;
A.wordSample=d=>d.section==='actRegister'?A.referenceTemplate(d):registerSample(d);
const registerPreview=A.wordPreview;
A.wordPreview=async d=>{const t=tpl(d.id);if(wordKey(t||{})!=='actRegister')return registerPreview(d);try{
 const {p}=wordUIContext(),v=volumeList(p).find(v=>v.s?.acts.some(a=>a.type==='АОСР')),a=v?.s.acts.find(a=>a.type==='АОСР');
 if(!a)throw Error('Создайте АОСР для предпросмотра реестра');
 const doc={id:'a'+a.id};registerMetadata(p,v,doc);const config=doc.actRegister;
 const [key,label,suffix]=ACT_REGISTERS.find(([k])=>config.settings[k]?.enabled&&config.entries[k]?.length)||ACT_REGISTERS.find(([k])=>config.entries[k]?.length)||[];
 if(!key)throw Error('Заполните перечень материалов, документов или приложений акта');
 const rows=config.entries[key],settings=config.settings[key]||{},values={...config.values,
  'Документ.Наименование':'Реестр '+label,'Документ.Номер':settings.number||a.num+'-'+suffix,
  'Документ.Дата':settings.date||config.values['АОСР.Дата'],'Реестр.КоличествоПозиций':String(rows.length),
  'Реестр.Текст':rows.map((text,i)=>(i+1)+'. '+text).join('\n'),'Документ.Содержание':rows.join('\n')};
 await nativeCall('openFilledWord',{key:t.fileKey,values,collections:{Реестр:rows.map((text,i)=>({Номер:i+1,Наименование:text,Тип:'',Номер_Дата:'',КоличествоСтраниц:'',Листы:''}))}});
 }catch(e){toast(e.message);}};
const registerActView=V.a;
V.a=r=>{const view=registerActView(r),a=getEnt('act',r[1]);if(!a||a.type!=='АОСР'||!['main',undefined].includes(r[2]))return view;
 const box=document.createElement('div');box.innerHTML=view;
 box.querySelector('.page')?.insertAdjacentHTML('beforeend',`<div class="card"><h3>Реестры к АОСР</h3><p>Полные перечни остаются в карточке. При переполнении приложение предложит вынести их в реестры. АОСР длиннее двух страниц не экспортируется.</p>${ACT_REGISTERS.map(([key,label,suffix])=>{const reg=a.registers?.[key]||{};return `<label class="row mb"><input type="checkbox" data-act-register="${key}" data-act="${a.id}" ${reg.enabled?'checked':''}>Вынести ${label} в реестр</label>${reg.enabled?`<div class="g2">${F('Номер реестра','act',a.id,'registers.'+key+'.number',reg.number||'',{placeholder:a.num+'-'+suffix})}${F('Дата (пусто — дата АОСР)','act',a.id,'registers.'+key+'.date',reg.date||'',{type:'date'})}</div>`:''}`;}).join('')}</div>`);return box.innerHTML;};
document.addEventListener('change',event=>{const el=event.target;if(!el.dataset.actRegister||!guard())return;const a=getEnt('act',el.dataset.act);a.registers=a.registers||{};a.registers[el.dataset.actRegister]={...a.registers[el.dataset.actRegister],enabled:el.checked};commit('Изменено включение реестра к АОСР',a);});

// Retry only after the user accepts concrete registers. No automatic truncation or font changes.
const printNativeCall=nativeCall;
let overflowDismiss=null;
const printCloseModal=closeModal;
closeModal=()=>{const dismiss=overflowDismiss;overflowDismiss=null;if(dismiss)dismiss(false);printCloseModal();};
nativeCall=async(op,params={})=>{
 for(;;){
  try{return await printNativeCall(op,params);}catch(error){
   if(!['exportPdf','exportPdfZip','exportRegistry','exportPrintFolder'].includes(op))throw error;
   const issues=(error.details||[]).filter(x=>x.kind==='actOverflow');
   if(!issues.length)throw error;
   const candidates=issues.filter(x=>x.actId&&x.suggested?.length);
   if(!candidates.length)throw error;
   const accepted=await new Promise(resolve=>{overflowDismiss=resolve;modal('АОСР не помещается в две страницы',
    `<p>Предлагаемые реестры сохранят полные перечни, а в акте останутся ссылки. После этого число страниц будет проверено повторно.</p>${issues.map(x=>`<p><b>${esc(x.number)}</b> — ${x.pages} стр.${x.suggested.length?'<br>Вынести в реестры: '+x.suggested.map(k=>esc(ACT_REGISTERS.find(r=>r[0]===k)[1])).join(', '):'<br>Все доступные реестры уже включены; требуется исправить текст или шаблон.'}</p>`).join('')}`,
    [{l:'Вернуться к карточкам',f:()=>resolve(false)},{l:'Применить и пересобрать',c:'pri',f:()=>resolve(true)}],'wide');});
   if(!accepted)return null;
   if(!guard())return null;
   for(const issue of candidates){const a=getEnt('act',issue.actId);if(!a)throw Error('Акт удалён');a.registers=a.registers||{};for(const k of issue.suggested)a.registers[k]={...a.registers[k],enabled:true};}
   commit('Вынесены перечни АОСР в реестры');await desktopFlush();
   for(const plan of params.plans?.map(x=>x.plan)||[params.plan])for(const v of plan.volumes)for(const doc of v.documents){
    if(!doc.actRegister)continue;const a=getEnt('act',doc.actRegister.actId);
    doc.actRegister.settings=structuredClone(a.registers||{});for(const reg of Object.values(doc.actRegister.settings))if(reg.date)reg.date=fmtD(reg.date);
   }
   modal('Повторная сборка','<p>Формирование реестров и проверка двух страниц АОСР…</p>',[]);
  }
 }
};

const printBuildView=V.build;
V.build=r=>{const view=printBuildView(r),p=proj(r[1])||S.projects[0];if(!p)return view;return view+`<div class="card"><h3>Комплект для печати</h3><p>Отдельные документы по порядку сборки, пачки PDF по формату и режиму печати и таблица комплектации.</p>${B('Подготовить папку для печати','printSetup',`data-p="${p.id}"`,'pri')}</div>`;};
let printSelection=null;
A.printSetup=d=>{try{const p=proj(d.p),c=assemblyPick(p);if(c.scenario==='11')throw Error('Выберите сценарий сборки PDF вместо переносимой базы');const plans=assemblyPlans(p,c),types=new Set();
 plans.forEach(entry=>entry.plan.volumes.forEach(v=>v.documents.forEach(doc=>{types.add(doc.type);if(doc.actRegister)for(const [,label] of ACT_REGISTERS)types.add('Реестр '+label);})));printSelection={p:d.p,plans};
 const opts=v=>[['simplex','Односторонняя'],['duplex','Двусторонняя']].map(([key,label])=>`<option value="${key}" ${v===key?'selected':''}>${label}</option>`).join('');
 modal('Настройки печати',`<p>Используются состав и порядок выбранного сценария сборки. Масштаб исходных листов сохраняется.</p><label class="row mb"><input type="checkbox" id="print-number">Сквозная нумерация страниц сборки</label><label>Переворот при двусторонней печати <select id="print-binding"><option value="long">По длинному краю</option><option value="short">По короткому краю</option></select></label><h3>По типам документов</h3>${[...types].map(t=>`<label class="row mb"><span class="grow">${esc(t)}</span><select data-print-type="${esc(t)}">${opts(t==='АОСР'?'duplex':'simplex')}</select></label>`).join('')}<p class="small mut">Пустые обороты между самостоятельными документами добавляются автоматически. Нумерация наносится на печатные пачки; отдельные PDF сохраняются без неё.</p>`,[{l:'Отмена'},{l:'Сформировать папку',c:'pri',f:()=>{A.printRun();return false;}}],'wide');
 }catch(e){toast(e.message);}};
A.printRun=async()=>{if(pdfExportBusy||!printSelection)return;const {plans}=printSelection;
 const options={numberPages:!!$('#print-number')?.checked,binding:$('#print-binding')?.value||'long',
  types:Object.fromEntries([...document.querySelectorAll('[data-print-type]')].map(el=>[el.dataset.printType,el.value]))};
 pdfExportBusy=true;try{await desktopFlush();if(!await confirmFrameWarnings(plans.map(x=>x.plan)))return;
  modal('Подготовка печатного комплекта','<p>Проверка документов, формирование реестров и печатных пачек…</p>',[]);
  const result=await desktopTrack(nativeCall('exportPrintFolder',{plans,options}));if(!result){closeModal();return;}
  modal('Папка для печати сохранена',`<p>${esc(result.path)}</p><p>${result.documents} документов · ${result.files} файлов</p>`,[{l:'Готово',c:'pri'}]);
 }catch(e){modal('Печать не подготовлена',`<div style="white-space:pre-wrap">${esc(e.message)}</div>`,[{l:'Закрыть'}],'wide');}finally{pdfExportBusy=false;}};

const importBaseView=libBase;
libBase=sel=>{const view=importBaseView(sel),box=document.createElement('div');box.innerHTML=view;box.querySelector('.page')?.insertAdjacentHTML('afterbegin',`<div class="card"><div class="row">${B('Импорт материалов из Excel','materialsImport','','pri')}${B('Скачать шаблон Excel','materialsTemplate')}</div><p class="small mut">Одна строка — один материал. Для каждого паспорта или сертификата заполните отдельную группу «Документ N». Указывайте путь к PDF относительно выбранной папки. Пустые группы пропускаются; дополнительные группы можно скопировать и пронумеровать. Обязательны наименование материала, тип и файл документа.</p></div>`);return box.innerHTML;};
A.materialsTemplate=async()=>{try{const r=await nativeCall('saveMaterialsTemplate');if(r)toast('Шаблон Excel сохранён');}catch(e){toast(e.message);}};
let materialImportPreview=null;
A.materialsImport=async()=>{if(!guard('lib'))return;try{await desktopFlush();const r=await nativeCall('previewMaterialsImport');if(!r)return;materialImportPreview=r;
 modal('Проверка импорта материалов',`${r.errors.length?'<div class="alert al-a" style="white-space:pre-wrap">'+esc(r.errors.join('\n'))+'</div><p>Импорт заблокирован. Исправьте Excel или файлы и повторите проверку.</p>':''}${r.items.map(item=>`<div class="card"><b>Строка ${item.row}: ${esc(item.name)} ${esc(item.brand)}</b><p>${item.docs.map(d=>esc(d.type+(d.num?' № '+d.num:'')+' — '+d.relative+' · '+d.pages+' стр.')).join('<br>')}</p><select data-import-row="${item.row}">${item.matches.length?'<option value="">Выберите действие</option>':''}<option value="new">Создать новый материал</option>${item.matches.map(m=>`<option value="${m.id}">Добавить документы к «${esc(m.name)} ${esc(m.brand)}»</option>`).join('')}</select></div>`).join('')}`,[{l:'Отмена'},...(!r.errors.length?[{l:'Импортировать',c:'pri',f:()=>{A.materialsCommit();return false;}}]:[])],'wide');
 }catch(e){modal('Импорт не выполнен','<p>'+esc(e.message)+'</p>',[{l:'Закрыть'}]);}};
A.materialsCommit=async()=>{if(!materialImportPreview||!guard('lib'))return;const choices=Object.fromEntries([...document.querySelectorAll('[data-import-row]')].map(el=>[el.dataset.importRow,el.value]));if(Object.values(choices).some(x=>!x)){toast('Выберите действие для каждого совпадения');return;}
 try{await desktopFlush();const result=await desktopTrack(nativeCall('commitMaterialsImport',{token:materialImportPreview.token,choices,revision:desktopRevision}));acceptFolder(result);materialImportPreview=null;closeModal();render();toast(`Импортировано материалов: ${result.importedMaterials}, документов: ${result.importedDocuments}. Повторов пропущено: ${result.skippedDocuments}`);}catch(e){modal('Импорт не выполнен','<p>'+esc(e.message)+'</p>',[{l:'Закрыть'}]);}};
