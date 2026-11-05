/* A reusable DOCX library; choices belong to each object and its customer profile. */
const WORD_SECTIONS=[
 ['title','Титульный лист','Титульный лист','Оформление комплекта'],
 ['reg','Реестр','Реестр / опись документов','Оформление комплекта'],
 ['orders','Организационный документ','Приказы, доверенности и организационные документы','Общая документация объекта'],
 ['ozhr','Общий журнал работ','Общий журнал работ','Общая документация объекта'],
 ['spj','Специальный журнал','Специальные журналы','Общая документация объекта'],
 ['aook','АООК','Акты ответственных конструкций — АООК','Общая документация объекта'],
 ['survey','Исполнительная съёмка','Исполнительные съёмки','Общая документация объекта'],
 ['aik','АИК','Акты входного контроля — АИК','Документы инженерных систем'],
 ['aosr','АОСР','Акты скрытых работ — АОСР','Документы инженерных систем'],
 ['photos','Фототаблица','Фототаблицы к актам','Документы инженерных систем'],
 ['schemes','Исполнительная схема','Исполнительные схемы','Документы инженерных систем'],
 ['tests','Акт испытаний / протокол','Акты испытаний и протоколы','Документы инженерных систем'],
 ['quality','Документ качества','Паспорта, сертификаты и декларации','Документы инженерных систем'],
 ['pass','Паспорт оборудования','Паспорта оборудования','Документация для эксплуатации'],
 ['instr','Документ для эксплуатации','Инструкции и документы для эксплуатации','Документация для эксплуатации'],
 ['other','Иной документ','Другие шаблоны','Дополнительно']
];
const WORD_FIELDS=[];
const wordOldEnsure=ensureWorkspace;ensureWorkspace=()=>{wordOldEnsure();if(!S)return;S.projects.forEach(p=>{p.wordTemplates=p.wordTemplates||{};p.wordProfileTemplates=p.wordProfileTemplates||{};});};
function wordKey(t){return t.section||WORD_SECTIONS.find(x=>x[1]===t.type)?.[0]||'other';}
function wordChoice(p,vol,key){
 const scope=vol.sp?.profileId,override=scope?p.wordProfileTemplates?.[scope]:null;
 const id=override?.[key]||p.wordTemplates?.[key]||'';
 if(!id||id==='__builtin__')return null;
 const t=tpl(id);return t||{id,name:'Шаблон удалён',section:key,fileKey:''};
}
function wordUIContext(){
 const p=proj(S.ui.wordObject)||S.projects[0]||null,profile=prof(S.ui.wordProfile);
 if(p){p.wordTemplates=p.wordTemplates||{};p.wordProfileTemplates=p.wordProfileTemplates||{};if(profile)p.wordProfileTemplates[profile.id]=p.wordProfileTemplates[profile.id]||{};}
 return {p,profile,map:p?(profile?p.wordProfileTemplates[profile.id]:p.wordTemplates):null};
}
function wordSectionBody(section,p,profile,map){
 const [key,type,label]=section,list=S.lib.templates.filter(t=>wordKey(t)===key),selected=map?.[key]||'',path=profile?'wordProfileTemplates.'+profile.id+'.'+key:'wordTemplates.'+key;
 const inherited=profile&&p?wordChoice(p,{},key):null;
 const effective=selected==='__builtin__'?null:tpl(selected)||inherited;
 const opts=[['',profile?'Как у объекта'+(inherited?' — '+inherited.name:' — стандартная форма'):'Стандартная форма приложения'],...(profile?[['__builtin__','Стандартная форма приложения']]:[]),...list.filter(t=>t.fileKey).map(t=>[t.id,t.name])];
 if(selected&&!opts.some(x=>x[0]===selected))opts.push([selected,'Файл выбранного шаблона отсутствует — загрузите DOCX']);
 return `<details class="word-section" ${(S.ui.wordOpen?.[key]??(key==='aosr'))?'open':''} data-word-section="${key}"><summary><span class="grow"><b>${esc(label)}</b><small>${effective?esc(effective.name):'Стандартная форма / загруженные PDF'}</small></span><span class="pill p-n">${list.filter(t=>t.fileKey).length} шаблонов</span>${ic('chev')}</summary><div class="word-body"><div class="word-choice">${p?F('Использовать при сборке ИД','proj',p.id,path,selected,{opts,rr:1}):'<p class="mut">Создайте объект, чтобы выбрать шаблон для сборки.</p>'}<div class="row">${B('Загрузить .docx','tplAdd',`data-section="${key}"`,'pri')}${B('Создать образец с тегами','wordSample',`data-section="${key}"`)}</div></div>${list.map(t=>{
 const unknown=(t.tags||[]).filter(tag=>!knownTags().has(tag)),chosen=t.id===selected;
 return `<article class="word-template ${chosen?'chosen':''}"><div class="grow"><div class="row">${F('','tpl',t.id,'name',t.name,{style:'flex:1;min-width:180px'})}${chosen?'<span class="pill p-g">Выбран</span>':''}</div><div class="small mut mt">${esc(t.file)} · ${t.tags?.length||0} тегов${t.fileKey?'':' · DOCX ещё не загружен'}</div>${unknown.length?`<div class="small" style="color:var(--red)">Неизвестные теги: ${esc(unknown.join(', '))}</div>`:''}<details class="word-tags"><summary>Поля шаблона</summary><div class="row mt">${(t.tags||[]).map(x=>`<code class="tag">{{${esc(x)}}}</code>`).join('')||'<span class="mut small">Фиксированный документ без тегов.</span>'}</div></details></div><div class="row word-actions">${t.fileKey?B('Открыть в Word','wordOpen',`data-id="${t.id}"`):''}${t.fileKey&&p?B('Заполнить и открыть','wordPreview',`data-id="${t.id}"`):''}${t.fileKey&&p&&!chosen?B('Выбрать','wordSelect',`data-id="${t.id}" data-section="${key}"`,'pri'):''}${B('Заменить файл','tplReplace',`data-id="${t.id}"`,'sm')}${B('Удалить','wordDelete',`data-id="${t.id}"`,'sm ghost')}</div></article>`;
 }).join('')||'<div class="word-empty">В этом разделе пока нет Word-шаблонов. Загрузите свой файл или создайте образец с тегами.</div>'}</div></details>`;
}
document.addEventListener('toggle',event=>{const node=event.target,key=node?.dataset?.wordSection;if(!key||!node.isConnected||!S)return;S.ui.wordOpen=S.ui.wordOpen||{};S.ui.wordOpen[key]=node.open;},true);
const wordOriginalProfiles=libProfiles;libProfiles=(tab,sel)=>{
 if(tab==='templates'){
  const {p,profile,map}=wordUIContext();
  return `<div class="page">${hdr('Профили и шаблоны','Шаблоны разложены по составу исполнительной документации')}${tabs('#/lib',tab,[['profiles','Профили заказчиков',S.lib.profiles.length],['templates','Шаблоны Word',S.lib.templates.length],['tags','Справочник тегов',knownTags().size]])}<div class="card word-scope"><div class="g2">${F('Объект','ui','','wordObject',p?.id||'',{opts:S.projects.map(p=>[p.id,p.name]),rr:1})}${F('Настройки шаблонов','ui','','wordProfile',profile?.id||'',{opts:[['','Базовый набор этого объекта'],...S.lib.profiles.map(x=>[x.id,x.name+' · v'+x.version])],rr:1})}</div><p class="small mut mt">${profile?'Настройки этого профиля действуют только на выбранном объекте, в томах с данным профилем заказчика.':'Выбранные шаблоны действуют только на этом объекте. Для профиля заказчика можно задать отдельные варианты.'}</p></div><p class="small mut mb">Откройте раздел → загрузите Word-шаблон → выберите его для сборки. Кнопка «Заполнить и открыть» подставляет данные выбранного объекта. Изменения исходного шаблона сохраняются в папке базы. Сохраните и закройте Word перед сборкой.</p>${[...new Set(WORD_SECTIONS.map(x=>x[3]))].map(group=>`<h2 class="word-group">${esc(group)}</h2>${WORD_SECTIONS.filter(x=>x[3]===group).map(x=>wordSectionBody(x,p,profile,map)).join('')}`).join('')}</div>`;
 }
 let body=wordOriginalProfiles(tab,sel);
 if(tab==='profiles')body=body.replace(/<div class="small mut"[^>]*>Шаблоны профиля<\/div><div class="lst">[\s\S]*?<\/div>/,`<div class="flow-note">Word-шаблоны выбираются отдельно для объекта и профиля во вкладке «Шаблоны Word». ${B('Выбрать шаблоны','wordChooseProfile',`data-id="${esc(sel||'')}"`,'sm')}</div>`);
 if(tab==='tags')body=body.replace('</tbody>',WORD_FIELDS.map(([tag,source])=>`<tr><td><code class="tag">{{${esc(tag)}}}</code></td><td class="t2">${esc(source)}</td><td class="small">Автоматически при сборке</td></tr>`).join('')+'</tbody>')+'';
 return body;
};
A.wordChooseProfile=d=>{S.ui.wordProfile=d.id||'';const used=S.projects.find(p=>p.systems.some(s=>s.subprofiles.some(sp=>sp.profileId===d.id)));S.ui.wordObject=used?.id||S.ui.wordObject;save();go('#/lib/templates');};
A.tplAdd=async d=>{if(!guard('lib'))return;try{const file=await desktopTrack(nativeCall('pickDocx'));if(!file)return;const section=WORD_SECTIONS.find(x=>x[0]===d?.section)||WORD_SECTIONS.at(-1);
 S.lib.templates.push({id:'t'+uid(),name:file.name.replace(/\.docx$/i,''),type:section[1],section:section[0],file:file.name,fileKey:file.id,tags:file.tags,locked:false,date:today()});
 commit('Загружен Word-шаблон «'+file.name+'»');await desktopFlush();toast('Word-файл сохранён в базе. Выберите его для сборки.');}catch(e){toast(e.message);}};
A.tplReplace=async d=>{if(!guard('lib'))return;try{const t=tpl(d.id),file=await desktopTrack(nativeCall('pickDocx'));if(!file||!t)return;
 Object.assign(t,{file:file.name,fileKey:file.id,tags:file.tags,date:today(),locked:false});commit('Обновлён Word-шаблон «'+t.name+'»',t);await desktopFlush();}catch(e){toast(e.message);}};
A.wordOpen=async d=>{try{const t=tpl(d.id);if(!t?.fileKey)throw Error('Сначала загрузите DOCX-файл');await nativeCall('openWordTemplate',{key:t.fileKey});}catch(e){toast(e.message);}};
A.wordSelect=async d=>{const {p,map}=wordUIContext();if(!p||!guard('obj:'+p.id))return;const t=tpl(d.id);if(!t?.fileKey)return;map[d.section]=t.id;commit('Выбран Word-шаблон «'+t.name+'» для '+p.name,p);await desktopFlush().catch(e=>toast(e.message));};
A.wordPreview=async d=>{try{const {p,profile}=wordUIContext(),t=tpl(d.id);if(!p||!t?.fileKey)throw Error('Выберите объект и загрузите DOCX');
 const vols=volumeList(p),base=vols.find(v=>v.s&&(!profile||v.sp.profileId===profile.id))||vols[0];
 let id=wordKey(t)==='reg'?'reg':'title';const key=wordKey(t),items=blocksFor(p,base).find(b=>b.key===key)?.items||[];
 if(key==='photos'){const a=base.s?.acts.find(a=>a.photos.length);if(a)id='p'+a.id;}else if(items.length)id=items[0].id;
 // Object-wide sections may live in Tom 1 even when the default preview volume is a system.
 const vol=items.length||['title','reg','photos'].includes(key)?base:vols.find(v=>blocksFor(p,v).some(b=>b.key===key&&b.items.length))||base;
 if(!['title','reg','photos'].includes(key))id=blocksFor(p,vol).find(b=>b.key===key)?.items[0]?.id||id;
 const context=validateDocumentContext(wordContext(p,vol,id),t.tags||[]);
 if(key==='reg'){context.collections.Реестр=registry(p,vol).rows.filter(r=>!r.book).map(r=>({Номер:r.n,Тип:r.type,Наименование:r.name,Номер_Дата:r.nd,КоличествоСтраниц:r.to-r.from+1,Листы:r.from===r.to?String(r.from):r.from+'-'+r.to}));context.values['Реестр.Текст']=context.values['Документ.Содержание']=context.collections.Реестр.map(r=>r.Номер+'. '+r.Наименование+' — '+r.Листы).join('\n');}
 await desktopTrack(nativeCall('openFilledWord',{key:t.fileKey,...context}));
 }catch(e){modal('Шаблон не заполнен','<p>'+esc(e.message)+'</p>',[{l:'Закрыть'}]);}};
A.wordSample=async d=>{if(!guard('lib'))return;try{const section=WORD_SECTIONS.find(x=>x[0]===d.section);if(!section)return;const f=await desktopTrack(nativeCall('sampleDocx',{section:section[0],title:section[2]}));
 const t={id:'t'+uid(),name:'Образец с тегами — '+section[2],type:section[1],section:section[0],file:f.name,fileKey:f.id,tags:f.tags,locked:false,date:today()};S.lib.templates.push(t);commit('Создан образец Word-шаблона',t);await desktopFlush();toast('Образец создан. Откройте в Word и настройте оформление.');}catch(e){toast(e.message);}};
A.wordDelete=d=>{const t=tpl(d.id);if(!t||!guard('lib'))return;confirmBox('Удалить Word-шаблон','Он будет перемещён в корзину. На объектах, где он выбран, будет включена стандартная форма.',()=>{
 S.projects.forEach(p=>{for(const map of [p.wordTemplates,...Object.values(p.wordProfileTemplates||{})])for(const key in map)if(map[key]===t.id)delete map[key];});toTrash('tpl',t.id);commit('Удалён Word-шаблон «'+t.name+'»');},'Удалить');};
const wordPreviousSources=pdfSources;pdfSources=(p,vol)=>{
 const sources=wordPreviousSources(p,vol);
 for(const block of blocksFor(p,vol))for(const item of block.items){
  const source=sources.get(item.id),key=item.id.startsWith('q')?(block.key==='pass'?'pass':'quality'):item.id.startsWith('p')&&item.type==='Фототаблица'?'photos':item.type==='АООК'?'aook':item.type.startsWith('АОСР')?'aosr':block.key;
  const t=wordChoice(p,vol,key);if(!t)continue;
  // Real uploaded PDFs (including signed scans) always remain originals in the assembled file.
  if(source?.kind==='pdf'&&(source.key||source.declaredFile)||source?.kind==='missing'&&item.id.startsWith('a')&&source.error?.includes('связи'))continue;
  if(!t.fileKey){sources.set(item.id,{kind:'missing',error:'загрузите файл выбранного Word-шаблона «'+t.name+'»'});continue;}
  let context;try{context=validateDocumentContext(wordContext(p,vol,item.id),t.tags||[]);}catch(e){sources.set(item.id,{kind:'missing',error:e.message});continue;}
  sources.set(item.id,{kind:item.id==='reg'?'registry':'word',templateKey:t.fileKey,templateName:t.name,...context});
 }
 return sources;
};
const wordOldBuild=V.build;V.build=r=>wordOldBuild(r).replace('Собрать и скачать PDF', 'Собрать и скачать PDF').replace('<h3>Состав и порядок',`<div class="row mb">${B('Word-шаблоны этого объекта','wordFromBuild','','sm')}</div><h3>Состав и порядок`);
A.wordFromBuild=()=>{const {p,vol}=curVol();S.ui.wordObject=p.id;S.ui.wordProfile=vol.sp?.profileId||'';save();go('#/lib/templates');};
const wordOldCheck=check;check=p=>{const result=wordOldCheck(p);result.E=result.E.filter(x=>!x.t.includes('нет шаблона обязательного документа'));return result;};
