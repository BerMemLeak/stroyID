/* A card history never replaces the working state just to display an old version. */
const historyKinds={proj:'projects',exec:'executions',sys:'systems',act:'acts',aik:'aik',jr:'journals',mat:'materials',base:'base',org:'orgs',per:'people',ord:'orders',pf:'profiles',tpl:'templates'};
const historyRoutes={p:'projects',e:'executions',s:'systems',a:'acts',k:'aik',j:'journals',m:'materials'};
const historyLib={orgs:'orgs',people:'people',orders:'orders',base:'base',profiles:'profiles',templates:'templates'};
const historyCache=new Map(),historyChecks=new Map();let historyIndex=null,historyIndexLoading=false;
const historyLabels={name:'Название',short:'Краткое название',num:'Номер',date:'Дата',start:'Начало работ',end:'Окончание работ',works:'Работы',place:'Место',rd:'Рабочая документация',norms:'Нормативы',next:'Последующие работы',note:'Примечание',quantityRows:'Объёмы работ',qty:'Количество',unit:'Единица',maker:'Производитель',brand:'Марка',docs:'Документы',schemes:'Схемы',tests:'Испытания',photos:'Фотографии',scan:'Подписанный акт',signers:'Подписанты',fileKey:'Файл',file:'Имя файла',sign:'Подпись',logo:'Логотип',photo:'Фото',img:'Изображение',attachments:'Вложения',status:'Статус',cipher:'Шифр',fio:'ФИО',fioShort:'Краткое ФИО',position:'Должность',authority:'Полномочия',quantityEnabled:'Ведомость включена'};
function historyField(path){return path.split('.').map(x=>historyLabels[x]||x).join(' → ');}
function historyTime(ts){const date=new Date(ts);return isNaN(date)?ts:date.toLocaleString('ru-RU');}
function historyBytes(n){return n>=1048576?(n/1048576).toFixed(1)+' МБ':Math.ceil(n/1024)+' КБ';}
function historyKey(ent,id){return historyKinds[ent]&&id?historyKinds[ent]+':'+id:null;}
function historyRouteKey(r=route()){
 if(r[0]==='history')return r[1]||null;
 if(r[0]==='e')return r[2]?'executions:'+r[2]:null;
 if(historyRoutes[r[0]]&&r[1])return historyRoutes[r[0]]+':'+r[1];
 if(r[0]==='lib'&&historyLib[r[1]]){
  const field=historyLib[r[1]],id=r[2]||S.ui.sel?.[r[1]];
  return id&&S.lib[field]?.some(x=>x.id===id)?field+':'+id:null;
 }return null;
}
function historyConflict(key){return folderConflicts.find(c=>c.key===key);}
function historyBlocked(key){return historyConflict(key)||folderWarnings.find(w=>w.key===key&&w.historyPending);}
async function historyFlush(){try{await desktopFlush(true);}catch(e){if(desktopDirty||!folderConflicts.length)throw e;}}
async function historyLoad(key,version=''){
 const cache=historyCache.get(key)||{};if(cache.loading)return;
 cache.loading=true;cache.error='';historyCache.set(key,cache);
 try{await historyFlush();if(!desktopDirty)acceptFolder(await nativeCall('poll'));cache.data=await desktopTrack(nativeCall('cardHistory',{key}));cache.detail=null;cache.version=version;
  if(version)cache.detail=await desktopTrack(nativeCall('cardHistoryVersion',{key,version}));
 }catch(e){cache.error=e.message;}finally{cache.loading=false;if(route()[0]==='history'&&route()[1]===key)render();}
}
A.historyOpen=async d=>{try{await historyFlush();const key=d.key||historyKey(d.ent,d.id);if(!key){go('#/history');return;}historyCache.delete(key);go('#/history/'+encodeURIComponent(key));await historyLoad(key);}catch(e){toast(e.message);}};
A.historyRefresh=async d=>{historyChecks.delete(d.key);await historyLoad(d.key);};
A.historyView=async d=>{await historyLoad(d.key,d.version);};
A.historyCurrent=d=>{const cache=historyCache.get(d.key);if(cache){cache.detail=null;cache.version='';}render();};
A.historyFile=async d=>{try{await desktopTrack(nativeCall('openHistoryAsset',{key:d.key,version:d.version,sha:d.sha}));}catch(e){toast(e.message);}};
function historyFileList(files,key,version){return files.map(f=>`<div class="row mb"><span class="grow">${esc(f.name)} <small>${f.ready?historyBytes(f.size):'Ожидается файл — синхронизация не завершена'}</small></span>${f.ready?B('Открыть файл','historyFile',`data-key="${esc(key)}" data-version="${version}" data-sha="${f.sha}"`,'sm'):''}</div>`).join('')||'<p class="small mut">Вложений нет.</p>';}
function historyValue(value){if(value===null||value===undefined)return '—';if(typeof value==='string'&&value.startsWith('data:'))return '[Изображение]';if(typeof value==='boolean')return value?'Да':'Нет';return typeof value==='object'?JSON.stringify(value,null,2):String(value);}
function historyPreview(record){
 if(!record)return '<p>В этой версии карточка удалена.</p>';
 const old=S,oldIX=IX;let html='';
 try{
  S=structuredClone(S);IX=null;const data=record.data;
  const find=(v)=>{if(Array.isArray(v)){const i=v.findIndex(x=>x&&x.id===data.id);if(i>=0){v[i]={...v[i],...structuredClone(data)};return true;}return v.some(find);}if(v&&typeof v==='object')return Object.values(v).some(find);return false;};
  if(!find(record.parent==='root'&&record.kind!=='projects'?S.lib[record.kind]:S.projects))throw Error('Карточка больше не находится в рабочем списке');
  S.ui.ro=true;
  const short={projects:'p',systems:'s',acts:'a',aik:'k',journals:'j',materials:'m'},lib={base:'base',orgs:'orgs',people:'people',orders:'orders',profiles:'profiles',templates:'templates'};
  if(short[record.kind])html=V[short[record.kind]]([short[record.kind],data.id]);
  else if(lib[record.kind])html=V.lib(['lib',lib[record.kind],data.id]);
  else throw Error('Поля карточки');
  const box=document.createElement('div');box.innerHTML=html;
  box.querySelectorAll('.tabs,.ph .acts,[data-a],a').forEach(x=>x.remove());
  box.querySelectorAll('input,select,textarea,button').forEach(x=>x.disabled=true);
  return box.innerHTML;
 }catch(e){return `<table class="tbl">${Object.entries(record.data).map(([k,v])=>`<tr><th>${esc(historyField(k))}</th><td><pre>${esc(historyValue(v))}</pre></td></tr>`).join('')}</table>`;}
 finally{S=old;IX=oldIX;}
}
function historyChanges(changes){return changes.length?`<table class="tbl history-diff"><thead><tr><th>Поле</th><th>Текущая карточка</th><th>Выбранная версия</th></tr></thead><tbody>${changes.map(x=>`<tr><td>${esc(historyField(x.field))}</td><td><pre>${esc(historyValue(x.before))}</pre></td><td><pre>${esc(historyValue(x.after))}</pre></td></tr>`).join('')}</tbody></table>`:'<p>Данные совпадают с текущей карточкой.</p>';}
A.historyRestore=d=>{
 const cache=historyCache.get(d.key),data=cache?.data,version=data?.versions.find(v=>v.id===d.version);if(!version||data.pending||S.ui.ro)return;
 confirmBox(data.conflict?'Выбрать итоговую версию':'Восстановить версию',data.conflict?'Выбранная карточка и её вложения станут итоговыми. Остальные варианты останутся в истории.':'Будет создана новая версия с этим содержимым. Последующие версии останутся в истории; к ним можно вернуться.',async()=>{
  try{await historyFlush();const result=await desktopTrack(nativeCall('cardHistoryRestore',{key:d.key,version:d.version,heads:data.heads,resolve:data.conflict,user:APP.user}));acceptFolder(result);desktopError='';desktopDirty=false;desktopPending=null;historyIndex=null;await historyLoad(d.key);render();toast('Версия выбрана и сохранена');}catch(e){toast(e.message);await historyLoad(d.key);}
 },'Использовать версию');
};
A.historyDelete=async d=>{
 if(S.ui.ro)return;const data=historyCache.get(d.key)?.data,versions=[...(historyChecks.get(d.key)||[])];if(data?.pending){toast('Дождитесь синхронизации версий');return;}if(!data||!versions.length){toast('Отметьте прошлые версии');return;}
 try{
  await historyFlush();const info=await desktopTrack(nativeCall('cardHistoryDelete',{key:d.key,versions,heads:data.heads,preview:true}));
  confirmBox('Удалить выбранные версии',`Будет удалено версий: ${info.versions}. Оценка освобождаемого места: ${historyBytes(info.bytes)}. Файлов, используемых другими версиями или резервными копиями: ${info.keptFiles}. Они сохранятся. Удаление передаётся на другие ПК через Яндекс Диск.`,async()=>{
   try{const result=await desktopTrack(nativeCall('cardHistoryDelete',{key:d.key,versions,heads:info.heads,user:APP.user}));acceptFolder(result);historyChecks.delete(d.key);desktopError='';historyIndex=null;await historyLoad(d.key);render();}catch(e){toast(e.message);await historyLoad(d.key);}
  },'Удалить версии');
 }catch(e){toast(e.message);}
};
document.addEventListener('change',event=>{const el=event.target;if(!el.dataset.historySelect)return;const key=el.dataset.key,set=historyChecks.get(key)||new Set();if(el.checked)set.add(el.dataset.historySelect);else set.delete(el.dataset.historySelect);historyChecks.set(key,set);});
V.history=r=>{
 const key=r[1];
 if(!key){
  if(!historyIndex&&!historyIndexLoading){historyIndexLoading=true;queueMicrotask(async()=>{try{historyIndex=await nativeCall('cardHistoryIndex');}catch(e){toast(e.message);historyIndex=[];}finally{historyIndexLoading=false;if(route()[0]==='history'&&!route()[1])render();}});}
  return `<div class="page">${hdr('История карточек','Каждая карточка восстанавливается отдельно')}${(historyIndex||[]).map(x=>`<div class="card row"><span class="grow"><b>${esc(x.title)}</b><br><small>${esc(x.path)}${x.conflicts?' · Конфликт: '+x.conflicts+' версий':''}</small></span>${B('История версий','historyOpen',`data-key="${esc(x.key)}"`)}</div>`).join('')||'<p>Загрузка карточек…</p>'}</div>`;
 }
 let cache=historyCache.get(key);
 if(!cache){cache={loading:true};historyCache.set(key,cache);queueMicrotask(()=>{cache.loading=false;historyLoad(key);});}
 const data=cache.data,detail=cache.detail;
 let body=`<div class="page">${hdr('История версий',esc(data?.path||key),B('Все карточки','nav','data-h="#/history"')+B('Обновить','historyRefresh',`data-key="${esc(key)}"`))}`;
 if(cache.error)body+=`<div class="alert al-r">${esc(cache.error)}</div>`;
 if(!data)return body+'<p>Загрузка истории…</p></div>';
 if(data.pending)body+='<div class="alert al-a">Ожидаются следующие версии карточки. Просмотр доступен; изменение истории временно недоступно.</div>';
 if(data.conflict)body+=`<div class="alert al-r"><b>Конфликт: ${data.heads.length} версий.</b> Редактирование карточки заблокировано. Посмотрите варианты и выберите один.</div>`;
 if(detail){const v=data.versions.find(x=>x.id===detail.id);body+=`<section class="card history-preview"><div class="row"><h3 class="grow">Просмотр версии ${v?.number} · ${esc(historyTime(v?.ts))}</h3>${B('Вернуться к текущей','historyCurrent',`data-key="${esc(key)}"`)}</div><p>Только просмотр. Рабочая карточка не изменена. Связанные справочники показаны в текущем состоянии.</p>${historyFileList(detail.files,key,detail.id)}${!S.ui.ro&&!data.pending&&detail.ready&&(!v?.deleted||data.conflict)&&(!data.conflict||v.current)?B(data.conflict?'Выбрать эту версию':'Восстановить эту версию','historyRestore',`data-key="${esc(key)}" data-version="${detail.id}"`,'pri'):''}<details open><summary>Отличия от текущей карточки</summary>${historyChanges(detail.changes)}</details><details open><summary>Карточка в выбранной версии</summary><div class="history-form">${historyPreview(detail.record)}</div></details></section>`;}
 body+=`<section class="card"><div class="row"><h3 class="grow">Линия сохранений</h3>${!S.ui.ro&&!data.pending?B('Удалить отмеченные версии','historyDelete',`data-key="${esc(key)}"`):''}</div><p class="small mut">Восстановление создаёт новую запись. Текущие и неразрешённые варианты удалить нельзя. Для освобождения места используйте удаление в приложении.</p><ol class="history-line">`;
 for(const v of data.versions){const attr=`data-key="${esc(key)}" data-version="${v.id}"`,checks=historyChecks.get(key);body+=`<li class="history-point ${v.current?'current':''}"><div class="row"><span class="grow"><b>Версия ${v.number}</b> · ${esc(historyTime(v.ts))}${v.current?` <span class="pill ${data.conflict?'p-r':'p-g'}">${data.conflict?'Вариант конфликта':'Текущая'}</span>`:''}</span>${!v.current&&!S.ui.ro?`<label><input type="checkbox" data-history-select="${v.id}" data-key="${esc(key)}" ${checks?.has(v.id)?'checked':''}> Удалить</label>`:''}</div><p>${esc(v.by||'Пользователь')} · ${esc(v.pc||'ПК')} · <code>${v.id.slice(0,8)}</code></p><p>${v.action==='restore'?'Восстановлена из версии '+esc(v.sourceVersion?.slice(0,8)):v.action==='resolve'?'Выбор итоговой версии':v.deleted?'Удаление карточки':v.changes.length?'Изменено: '+esc(v.changes.slice(0,6).map(historyField).join(', ')):'Сохранение карточки'}${v.parents.length>1?' · Объединение '+v.parents.length+' веток':''}</p>${v.parents.length?'<p class="small mut">Предыдущие версии: '+v.parents.map(id=>{const parent=data.versions.find(p=>p.id===id);return parent?'№ '+parent.number+' ('+id.slice(0,8)+')':'удалённая ('+id.slice(0,8)+')';}).join(', ')+'</p>':''}${!v.ready?'<p class="alert al-a">Ожидаются файлы Яндекс Диска</p>':''}<div class="row">${B('Посмотреть','historyView',attr,'sm')}${data.conflict&&v.current&&v.ready&&!S.ui.ro?B('Выбрать эту версию','historyRestore',attr,'pri sm'):''}</div></li>`;}
 return body+'</ol></section></div>';
};
const historyBaseSync=V.sync;V.sync=()=>historyBaseSync().replace('сохраняются обе версии','сохраняются все версии').replace('Выберите нужную после сравнения.','Выберите нужную после сравнения. <a href="#/history">История всех карточек</a>');
const historyTree=renderTree;renderTree=()=>{historyTree();if(!$('#tree a[href="#/history"]'))$('#tree').insertAdjacentHTML('beforeend',`<div class="tn"><a href="#/history">${ic('clock')}Версии карточек</a></div>`);};
const historyGuard=guard;guard=key=>{if(!historyGuard(key))return false;const current=historyRouteKey(),normal=key?.startsWith('sys:')?'systems:'+key.slice(4):key?.startsWith('obj:')?'projects:'+key.slice(4):null,conflict=historyBlocked(current)||historyBlocked(normal);if(conflict){toast('Карточка заблокирована. Выберите итоговую версию в истории.');return false;}return true;};
const historyRender=render;render=()=>{
 historyRender();const content=$('#content');if(!content||route()[0]==='history')return;
 const first=content.querySelector('[data-ent]:not([data-ent="ui"]):not([data-ent="root"]):not([data-ent="app"])');
 const key=historyRouteKey()||historyKey(first?.dataset.ent,first?.dataset.id),conflict=historyBlocked(key),page=content.querySelector('.page');
 if(key&&page){const header=page.querySelector('.ph .acts')||page.querySelector('.ph');if(header&&!header.querySelector('[data-a="historyOpen"]'))header.insertAdjacentHTML('beforeend',B('История версий','historyOpen',`data-key="${esc(key)}"`));
  if(conflict){page.insertAdjacentHTML('afterbegin',`<div class="alert al-r" data-history-locked>${conflict.historyPending?'Ожидается следующая версия.':'Конфликт: '+conflict.versions.length+' версий.'} Редактирование заблокировано. ${B('Выбрать версию','historyOpen',`data-key="${esc(key)}"`,'sm')}</div>`);page.querySelectorAll('input:not([data-ent="ui"]),select:not([data-ent="ui"]),textarea,button[data-a]').forEach(el=>{if(!['historyOpen','openBlob','nav','roToggle'].includes(el.dataset.a))el.disabled=true;});}
 }
 // The same badge appears in act lists, libraries and the navigation tree.
 document.querySelectorAll('#content [data-h],#content a[href^="#/"],#tree a[href^="#/"]').forEach(el=>{const h=el.dataset.h||el.getAttribute('href');let r;try{r=decodeURIComponent(h.replace(/^#\/?/, '')).split('/');}catch(e){return;}const c=historyConflict(historyRouteKey(r));if(c&&!el.querySelector('[data-history-badge]'))el.insertAdjacentHTML('beforeend',` <span class="pill p-r" data-history-badge>Конфликт: ${c.versions.length}</span>`);});
 if(route()[0]==='sync')folderConflicts.forEach(c=>{const cards=[...content.querySelectorAll('.card')],card=cards.find(x=>x.querySelector('h3')?.textContent==='Конфликт карточки'&&x.querySelector('p')?.textContent===c.path);if(card){card.innerHTML=`<h3>Конфликт: ${c.versions.length} версий</h3><p>${esc(c.path)}</p>${B('Сравнить и выбрать версию','historyOpen',`data-key="${esc(c.key)}"`,'pri')}`;}});
};
// Capture edits before legacy handlers that do not carry the card key to guard().
for(const eventName of ['input','change','click'])document.addEventListener(eventName,event=>{
 const el=event.target.closest('[data-ent],[data-a]');if(!el||!$('#content')?.contains(el)||route()[0]==='history')return;
 const key=historyKey(el.dataset.ent,el.dataset.id),c=historyBlocked(key||historyRouteKey());
 if(c&&!['historyOpen','openBlob','nav','roToggle'].includes(el.dataset.a)&&el.dataset.ent!=='ui'){event.preventDefault();event.stopImmediatePropagation();toast('Выберите итоговую версию конфликтующей карточки');}
},true);
