/* All document values are resolved here. No legacy aliases or post-fill overrides. */
const DOCUMENT_ROLES=DOCUMENT_TAG_SCHEMA.roles;
const PARTICIPANT_FIELDS={Генподрядчик:'genContractor',Застройщик:'developer',Техзаказчик:'techCustomer',Проектировщик:'designOrg',АвторскийНадзор:'supervision',Эксплуатация:'operator'};
function documentProfile(s,a,v={}){
 if(!s)return null;
 const selected=s.subprofiles.find(x=>x.id===v.sp?.id);
 if(selected&&(!a||a.subs.includes(selected.id)))return selected;
 if(a){const assigned=s.subprofiles.filter(x=>a.subs.includes(x.id));return assigned.length===1?assigned[0]:null;}
 return null;
}
function documentIdentity(p,v={},id='title'){
 let found=null;
 const offer=(entry)=>{if(found)throw Error('Неоднозначный идентификатор документа: '+id);found=entry;};
 for(const s of p.systems){
  for(const a of s.acts){
   if(['a'+a.id,'p'+a.id,'quantity:'+a.id].includes(id))offer({s,a,record:a,kind:id.startsWith('quantity:')?'quantity':id==='p'+a.id?'photos':'act'});
   for(const [key,prefix] of [['schemes','c'],['tests','t']])for(const r of a[key])if(id===prefix+r.id)offer({s,a,record:r,kind:key});
  }
  for(const k of s.aik)if(id==='k'+k.id)offer({s,k,record:k,kind:'aik',m:pMat(p,k.materialId)});
  for(const [key,prefix] of [['sketches','sk'],['trials','trial'],['journals','j']])for(const r of s[key])if(id===prefix+r.id)offer({s,record:r,j:key==='journals'?r:null,kind:key});
  if(id==='ss'+s.id)offer({s,record:s.scheme,kind:'schemes'});
 }
 for(const [key,prefix] of [['admin','admin'],['surveys','v'],['opsDocs','op'],['journals','j']])for(const r of p[key])if(id===prefix+r.id)offer({record:r,j:key==='journals'?r:null,kind:key});
 for(const m of p.materials)for(const r of mDocs(m))if(id==='q'+r.id||id.startsWith('q'+r.id+'_')){const owner=id==='q'+r.id?null:p.systems.flatMap(s=>s.acts.map(a=>({s,a}))).find(x=>id==='q'+r.id+'_'+x.a.id);offer({record:r,m,kind:'quality',...owner});}
 if(!found&&!['title','reg'].includes(id))throw Error('Документ не найден: '+id);
 const c=found||{kind:id,s:v.s? p.systems.find(x=>x.id===v.s.id):null};
 c.p=p;c.v=v;c.id=id;c.sp=documentProfile(c.s,c.a,v);
 const eid=c.a?.executionId||c.k?.executionId||c.record?.executionId||v.executionId;
 c.execution=execution(p,eid)||null;
 return c;
}
function documentOrganization(p,role){
 const field=PARTICIPANT_FIELDS[role],explicit=p.participantOrgs?.[role];
 if(explicit)return org(explicit)||null;
 const name=(p[field]||'').trim(),matches=S.lib.orgs.filter(o=>name&&[o.full,o.short].includes(name));
 // Existing free text remains printable; never guess between duplicate names.
 return matches.length===1?matches[0]:{full:name};
}
function documentValues(c){
 const {p,v,a,k,s,j,m,record:r,sp}=c,values={},origins={},issues=[];
 for(const [tag,meta] of Object.entries(DOCUMENT_TAG_SCHEMA.fields))if(meta.type!=='collection')values[tag]='';
 const put=(tag,value,source,ref)=>{if(!(tag in values))throw Error('Тег отсутствует в справочнике: '+tag);values[tag]=value??'';origins[tag]={source,ref:ref||('#/p/'+p.id+'/general')};};
 const actRef=a?'#/a/'+a.id+'/main':'',docRef=actRef||(s?'#/s/'+s.id+'/params':'#/p/'+p.id+'/general');
 const date=(tag,raw,source,ref)=>{
  if(!raw)return;
  const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(raw),d=match&&new Date(raw+'T12:00:00Z');
  if(!match||isNaN(d)||d.toISOString().slice(0,10)!==raw){issues.push({tag,message:'Некорректная дата: '+raw,ref:ref||docRef});return;}
  const [,year,month,day]=match,word=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'][Number(month)-1];
  put(tag,day+'.'+month+'.'+year,source,ref);
  for(const [key,value] of Object.entries({День:day,Месяц:month,МесяцПрописью:word,Год:year,Прописью:day+' '+word+' '+year+' г.'}))put(tag+'.'+key,value,source,ref);
 };
 const organization=(prefix,o,source,ref)=>{
  const data={Наименование:o?.full||o?.short||'',КраткоеНаименование:o?.short||o?.full||'',ИНН:o?.inn,КПП:o?.kpp,ОГРН:o?.ogrn,Адрес:o?.address,Телефон:o?.phone,Email:o?.email,СРО:o?.sro};
  data.Реквизиты=[data.Наименование,o?.ogrn?'ОГРН '+o.ogrn:'',o?.inn?'ИНН '+o.inn:'',o?.kpp?'КПП '+o.kpp:'',o?.address,o?.phone,o?.sro].filter(Boolean).join(', ');
  for(const [key,value] of Object.entries(data))put(prefix+'.'+key,value,source,ref);
 };
 for(const [key,field] of Object.entries({Наименование:'name',Адрес:'address',Шифр:'cipher',Договор:'contract'}))put('Объект.'+key,p[field],'Карточка объекта');
 for(const [role,field] of Object.entries(PARTICIPANT_FIELDS)){
  organization('Участники.'+role,documentOrganization(p,role),'Участники объекта: '+role);
  if(p.participantOrgs?.[role]&&!org(p.participantOrgs[role]))issues.push({tag:'Участники.'+role+'.Наименование',message:'Назначенная организация удалена',ref:'#/p/'+p.id+'/general'});
 }
 const issuer=org(p.exportIssuer),recipient=org(p.exportCustomer);
 organization('Комплект.Компания',issuer,'Компания выпуска комплекта');organization('Комплект.Получатель',recipient,'Получатель комплекта');
 for(const [field,tag] of [['exportIssuer','Комплект.Компания.Наименование'],['exportCustomer','Комплект.Получатель.Наименование']])if(p[field]&&!org(p[field]))issues.push({tag,message:'Выбранная организация удалена',ref:'#/build/'+p.id});
 put('Комплект.Наименование',v.title,'Выбранный том');put('Комплект.Год',p.documentYear||new Date().getFullYear(),'Год комплекта');put('Комплект.Город',p.documentCity,'Настройки объекта');put('Комплект.Логотип',c.kind==='title'?(issuer?issuer.logo:p.logo)||'':'','Компания выпуска / объект');
 for(const [key,field] of Object.entries({Шифр:'cipher',Код:'code',Наименование:'name'}))put('Раздел.'+key,s?.[field],'Раздел документа',docRef);
 date('Раздел.Дата',s?.sectionDate,'Дата раздела',docRef);
 const e=c.execution;put('Выполнение.Наименование',e?.name,'Выполнение документа',docRef);
 for(const [key,field] of Object.entries({Дата:'date',Начало:'start',Окончание:'end'}))date('Выполнение.'+key,e?.[field],'Выполнение документа',docRef);
 if(a){
  for(const [key,field] of Object.entries({Номер:'num',Работы:'works',МестоРабот:'place',РабочаяДокументация:'rd',Нормативы:'norms',ПоследующиеРаботы:'next',ДополнительныеСведения:'note',КоличествоЭкземпляров:'copies'}))put('АОСР.'+key,a[field],'Карточка акта '+a.num,actRef);
  for(const [key,field] of Object.entries({Дата:'date',Начало:'start',Окончание:'end'}))date('АОСР.'+key,a[field],'Карточка акта '+a.num,actRef);
  const mats=a.materials.map(id=>pMat(p,id));
  if(mats.some(x=>!x))issues.push({tag:'АОСР.Материалы',message:'Материал акта удалён',ref:'#/a/'+a.id+'/mat'});
  put('АОСР.Материалы',mats.filter(Boolean).map(x=>[mName(x),mDocs(x).map(d=>[d.type,d.num?'№ '+d.num:'',d.date?'от '+fmtD(d.date):''].filter(Boolean).join(' ')).join('; ')].filter(Boolean).join(' — ')).join('; '),'Материалы текущего акта',actRef);
  put('АОСР.Приложения',actAttachmentEntries(a,s).map((x,i)=>(i+1)+'. '+x.name+(x.pages?', '+x.pages+' л.':'')).join('\n'),'Приложения текущего акта',actRef);
  // Point 4 deliberately excludes quantity statements, photos and certificates.
  const evidence=[...a.schemes.map(x=>({name:['Исполнительная схема',x.num?'№ '+x.num:'',x.name].filter(Boolean).join(' '),pages:x.pages})),...linkedSchemes(a,s).filter(x=>x.item).map(({link,item})=>({name:'Исполнительная схема '+(item.record.num||item.name),pages:Number(link.to)-Number(link.from)+1})),...a.tests,...a.testLinks.map(id=>s.trials.find(x=>x.id===id)).filter(Boolean)];
  put('АОСР.ПодтверждающиеДокументы',evidence.map((x,i)=>(i+1)+'. '+[x.name,x.num?'№ '+x.num:'',x.date?'от '+fmtD(x.date):'',x.pages?x.pages+' л.':''].filter(Boolean).join(' ')).join('\n'),'Схемы и испытания акта',actRef);
 }
 if(k){put('АИК.Номер',k.num,'Карточка АИК',docRef);date('АИК.Дата',k.date,'Карточка АИК',docRef);put('АИК.Материал',mName(m),'Материал АИК',docRef);put('АИК.Количество',k.qty,'Карточка АИК',docRef);}
 const title=c.kind==='quantity'?quantityName(a):c.kind==='title'?v.title:c.kind==='reg'?'Реестр документов':r?.name||j?.name||a?.works||(k?'Входной контроль: '+mName(m):'');
 put('Документ.Наименование',title,'Текущий документ',docRef);put('Документ.Номер',r?.num,'Текущий документ',docRef);date('Документ.Дата',r?.date,'Текущий документ',docRef);put('Документ.Тип',a?.type||r?.type|| (k?'АИК':''),'Текущий документ',docRef);put('Документ.Примечание',r?.note,'Текущий документ',docRef);
 put('Документ.ДокументыКачества',(m?mDocs(m):a?a.materials.map(x=>pMat(p,x)).filter(Boolean).flatMap(mDocs):[]).map(x=>[x.type,x.num?'№ '+x.num:'',x.date?'от '+fmtD(x.date):''].filter(Boolean).join(' ')).join('; '),'Документы связанных материалов',docRef);
 put('Документ.Содержание',j?j.rows.map((r,i)=>(i+1)+'. '+j.cols.map((col,k)=>col+': '+(r.c[k]??'')).join('; ')).join('\n'):'','Строки журнала',docRef);
 DOCUMENT_ROLES.forEach((role,i)=>{
  const explicit=a?.signers?.['r'+i],pid=explicit||sp?.signers?.['r'+i],per=person(pid),prefix='Подписанты.'+role;
  const source=explicit?'Назначение в акте '+a.num:sp?'Комплект подписантов «'+sp.name+'»':'Роль не назначена';
  if(pid&&!per)issues.push({tag:prefix+'.ФИО',message:'Назначенный подписант удалён',ref:actRef||docRef});
  if(per?.orgId&&!org(per.orgId))issues.push({tag:prefix+'.Организация.Наименование',message:'Организация подписанта удалена',ref:actRef||docRef});
  if(a&&!explicit&&!sp&&a.subs.length>1)issues.push({tag:prefix+'.ФИО',message:'Выберите комплект подписантов этого акта',ref:actRef});
  const fio=per?.fio||per?.fioShort||'',short=per?.fioShort||shortFio(fio),o=org(per?.orgId);
  for(const [key,value] of Object.entries({ФИО:fio,ФамилияИнициалы:short,Должность:per?.position,ОснованиеПолномочий:per?.authority,НРС:per?.nrs,Описание:[per?.position,fio,o?.full||o?.short,per?.authority,per?.nrs?'НРС '+per.nrs:''].filter(Boolean).join(', ')}))put(prefix+'.'+key,value,source,actRef||docRef);
  organization(prefix+'.Организация',o,source+' → организация выбранного человека',actRef||docRef);
 });
 const collections={Строки:j?j.rows.map((r,i)=>Object.fromEntries([['Номер',i+1],...j.cols.map((_,k)=>['Колонка_'+(k+1),r.c[k]??''])])):[],Фото:a?a.photos.map((ph,i)=>({Номер:i+1,Подпись:ph.cap||'',Изображение:ph.img||''})):[],Реестр:[],Объемы:[]};
 if(a){
  for(const [key,value] of Object.entries({Наименование:quantityName(a),Проект:a.rd||s.cipher||p.cipher||'',Основание:a.rd,Примечание:a.quantityNote}))put('Ведомость.'+key,value,'Ведомость акта '+a.num,actRef);
  collections.Объемы=quantityRows(a).map((r,i)=>({Номер:i+1,Наименование:r.name||a.works||'',Место:r.place||'',Единица:r.unit||'',Количество:String(r.qty??'')}));
 }
 const custom=new Set();for(const x of p.extra){const tag='ДопПоля.'+slug(x.k);if(custom.has(tag))throw Error('Повторяется дополнительный тег '+tag);custom.add(tag);values[tag]=x.v??'';origins[tag]={source:'Дополнительное поле: '+x.k,ref:'#/p/'+p.id+'/general'};}
 return {values,collections,issues,bindings:Object.entries(values).map(([tag,value])=>({tag,value,...(origins[tag]||{source:DOCUMENT_TAG_SCHEMA.fields[tag]?.source,ref:docRef})}))};
}
function wordContext(p,v={},id='title'){return documentValues(documentIdentity(p,v,id));}
knownTags=()=>new Set([...Object.keys(DOCUMENT_TAG_SCHEMA.fields).filter(k=>DOCUMENT_TAG_SCHEMA.fields[k].type!=='frame'),...S.projects.flatMap(p=>p.extra.map(x=>'ДопПоля.'+slug(x.k)))]);
function validateDocumentContext(context,tags){
 const missing=tags.filter(t=>!Object.hasOwn(context.values,t)&&!Object.keys(DOCUMENT_TAG_SCHEMA.collections).some(g=>DOCUMENT_TAG_SCHEMA.collections[g].some(k=>t===g+'.'+k)));
 const problems=context.issues.filter(x=>tags.includes(x.tag)||tags.some(t=>t.startsWith(x.tag.split('.').slice(0,2).join('.')+'.'))).map(x=>x.message+' ({{'+x.tag+'}})');
 for(const tag of tags)if(DOCUMENT_TAG_SCHEMA.fields[tag]?.required&&String(context.values[tag]??'').trim()==='')problems.push('Не заполнено {{'+tag+'}}');
 if(missing.length)problems.unshift('Шаблон содержит неподдерживаемые теги: '+missing.map(x=>'{{'+x+'}}').join(', ')+'. Замените их по справочнику тегов.');
 if(problems.length)throw Error([...new Set(problems)].join('\n'));
 return context;
}
const documentTagProfiles=libProfiles;
libProfiles=(tab,sel)=>{
 if(tab!=='tags')return documentTagProfiles(tab,sel);
 const p=proj(S.ui.wordObject)||S.projects[0],vols=p?volumeList(p):[],v=vols.find(x=>x.key===S.ui.tagVolume)||vols.find(x=>x.s)||vols[0],acts=v?.s?.acts.filter(a=>!v.executionId||a.executionId===v.executionId)||[],a=acts.find(x=>x.id===S.ui.tagAct)||acts[0];
 const context=p?wordContext(p,v||{},a?'a'+a.id:'title'):null,byTag=new Map(context?.bindings.map(x=>[x.tag,x])||[]);
 return `<div class="page">${hdr('Справочник и проверка тегов','Единый набор тегов v2. Старые имена не поддерживаются.')}${tabs('#/lib',tab,[['profiles','Профили заказчиков'],['templates','Шаблоны Word'],['tags','Справочник тегов']])}<div class="card g3">${F('Объект','ui','','wordObject',p?.id||'',{opts:S.projects.map(p=>[p.id,p.name]),rr:1})}${F('Том / комплект подписантов','ui','','tagVolume',v?.key||'',{opts:vols.map(v=>[v.key,v.title]),rr:1})}${F('Акт для проверки','ui','','tagAct',a?.id||'',{opts:acts.map(a=>[a.id,a.num]),rr:1})}</div>${context?.issues.length?`<div class="alert al-a">${context.issues.map(x=>`<div>${esc(x.message)} · <a href="${esc(x.ref)}">Исправить</a></div>`).join('')}</div>`:''}<div class="tw"><table class="tbl" style="table-layout:fixed;width:100%;overflow-wrap:anywhere"><colgroup><col style="width:37%"><col style="width:22%"><col style="width:27%"><col style="width:14%"></colgroup><thead><tr><th>Тег</th><th>Источник</th><th>Значение</th><th>Если пусто</th></tr></thead><tbody>${[...Object.entries(DOCUMENT_TAG_SCHEMA.fields),...(p?.extra||[]).map(x=>['ДопПоля.'+slug(x.k),{source:'Дополнительное поле',empty:'blank'}])].map(([tag,meta])=>{const b=byTag.get(tag);return `<tr><td><code style="white-space:normal">{{${esc(tag)}}}</code></td><td>${b?.ref?`<a href="${esc(b.ref)}">${esc(b.source)}</a>`:esc(meta.source)}</td><td style="white-space:pre-wrap">${meta.type==='image'?(b?.value?'Изображение':'—'):meta.type==='collection'?'Повторяемая строка':esc(String(b?.value??'—'))}</td><td>${meta.empty==='error'?'Указать значение':meta.type==='frame'?'Рассчитывается для листа':'Пустое поле допустимо'}</td></tr>`;}).join('')}</tbody></table></div></div>`;
};
// Store participant links as IDs. Existing names remain readable until selected.
const tagProjectView=V.p;V.p=r=>{
 const html=tagProjectView(r),p=proj(r[1]);if(!p||!['general',undefined].includes(r[2]))return html;
 const box=document.createElement('div');box.innerHTML=html;
 for(const [role,field] of Object.entries(PARTICIPANT_FIELDS)){
  const input=box.querySelector(`[data-ent="proj"][data-f="${field}"]`);if(!input)continue;
  const selected=p.participantOrgs?.[role]||'',select=document.createElement('select');select.dataset.participantRole=role;select.dataset.p=p.id;
  select.innerHTML=`<option value="">${esc(p[field]?'Текущее название: '+p[field]:'Выберите организацию')}</option>`+(selected&&!org(selected)?`<option selected value="${esc(selected)}">Организация удалена</option>`:'')+S.lib.orgs.map(o=>`<option value="${esc(o.id)}" ${selected===o.id?'selected':''}>${esc(o.full||o.short)}</option>`).join('');input.replaceWith(select);
 }
 box.querySelector('.page')?.insertAdjacentHTML('beforeend',`<div class="card g2">${F('Город на титульном листе','proj',p.id,'documentCity',p.documentCity||'')}${F('Год комплекта (пусто — текущий)','proj',p.id,'documentYear',p.documentYear||'')}</div>`);
 return box.innerHTML;
};
document.addEventListener('change',event=>{const role=event.target.dataset.participantRole;if(!role)return;const p=proj(event.target.dataset.p);if(!guard('obj:'+p.id))return;p.participantOrgs=p.participantOrgs||{};p.participantOrgs[role]=event.target.value;const o=org(event.target.value);if(o)p[PARTICIPANT_FIELDS[role]]=o.full||o.short||'';commit('Изменён участник строительства',p);});
function documentActHtml(a,p,s,sp){
 const ctx=documentValues({...documentIdentity(p,{s,sp,executionId:a.executionId},'a'+a.id),a,record:a}),get=tag=>esc(String(ctx.values[tag]??'')).replace(/\n/g,'<br>'),line=(label,tag)=>`<div><b>${label}</b></div><div class="pl">${get(tag)||'&nbsp;'}</div>`;
 return `<div class="paper">${line('Объект капитального строительства','Объект.Наименование')}${line('Адрес объекта','Объект.Адрес')}${line('Застройщик','Участники.Застройщик.Реквизиты')}${line('Технический заказчик','Участники.Техзаказчик.Реквизиты')}${line('Лицо, осуществляющее строительство','Участники.Генподрядчик.Реквизиты')}${line('Лицо, осуществляющее подготовку проектной документации','Участники.Проектировщик.Реквизиты')}<h2>АКТ</h2><p align="center">${a.type==='АООК'?'освидетельствования ответственных конструкций':'освидетельствования скрытых работ'}</p><p>№ ${get('АОСР.Номер')} от ${get('АОСР.Дата.Прописью')}</p>${DOCUMENT_ROLES.map((role,i)=>line(esc(DOC_ROLES[i]),'Подписанты.'+role+'.Описание')).join('')}<p>Произвели осмотр работ, выполненных ${get('Подписанты.ИсполнительРабот.Организация.Наименование')}</p>${line('1. К освидетельствованию предъявлены работы','АОСР.Работы')}${line('Место выполнения работ','АОСР.МестоРабот')}${line('2. Работы выполнены по проектной документации','АОСР.РабочаяДокументация')}${line('3. При выполнении работ применены','АОСР.Материалы')}${line('4. Предъявлены документы, подтверждающие соответствие работ','АОСР.ПодтверждающиеДокументы')}<p>5. Начало работ: ${get('АОСР.Начало')}. Окончание: ${get('АОСР.Окончание')}.</p>${line('6. Работы выполнены в соответствии с','АОСР.Нормативы')}${line('7. Разрешается производство последующих работ','АОСР.ПоследующиеРаботы')}${line('Дополнительные сведения','АОСР.ДополнительныеСведения')}<p>Акт составлен в ${get('АОСР.КоличествоЭкземпляров')||'___'} экземплярах.</p>${line('Приложения','АОСР.Приложения')}<table>${DOCUMENT_ROLES.map((role,i)=>`<tr><td>${esc(ROLE_SH[i])}</td><td>________________</td><td>${get('Подписанты.'+role+'.ФамилияИнициалы')}</td></tr>`).join('')}</table></div>`;
}
aosrHtml=documentActHtml;
pdfTitle=(p,v)=>{const c=wordContext(p,v,'title'),g=t=>esc(String(c.values[t]??''));return `${c.values['Комплект.Логотип']?'<p align="right"><img src="'+esc(c.values['Комплект.Логотип'])+'" width="150"></p>':''}<p align="center">${g('Комплект.Компания.Реквизиты')}</p><h1>ИСПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ</h1><p align="center">${g('Объект.Наименование')}</p><p align="center">${g('Объект.Адрес')}</p><h2>${g('Комплект.Наименование')}</h2><p>Проект: ${g('Раздел.Шифр')||g('Объект.Шифр')}</p><p>${g('Раздел.Наименование')}</p><p>Заказчик: ${g('Участники.Техзаказчик.Наименование')}</p><p>Генеральный подрядчик: ${g('Участники.Генподрядчик.Наименование')}</p><p>Получатель комплекта: ${g('Комплект.Получатель.Наименование')}</p><p align="center">${g('Комплект.Город')} ${g('Комплект.Год')}</p>`;};
A.titlePrev=()=>{const {p,vol}=curVol();modal('Титульный лист',pdfTitle(p,vol),[{l:'Закрыть'}],'wide');};
const tagActView=V.a;V.a=r=>{const html=tagActView(r),c=ctx('act',r[1]);if(!c.o||!['main',undefined].includes(r[2]))return html;const box=document.createElement('div');box.innerHTML=html;box.querySelector('.page')?.insertAdjacentHTML('beforeend',`<div class="card">${F('Количество экземпляров акта (необязательно)','act',c.o.id,'copies',c.o.copies??'',{type:'number'})}</div>`);return box.innerHTML;};
const tagSources=pdfSources;pdfSources=(p,v)=>{
 const sources=tagSources(p,v);
 // Apply the same validation to generated standard forms; uploaded scans stay originals.
 for(const s of p.systems)for(const a of s.acts){
  const id='a'+a.id,source=sources.get(id);if(source?.kind!=='html')continue;
  try{const c=wordContext(p,v,id);validateDocumentContext(c,['Объект.Наименование','АОСР.Номер','АОСР.Дата','АОСР.Работы',...c.issues.map(x=>x.tag)]);}
  catch(e){sources.set(id,{kind:'missing',error:e.message});}
 }
 return sources;
};
function documentAikHtml(k,p,s){
 const c=wordContext(p,{s,executionId:k.executionId},'k'+k.id),g=t=>esc(String(c.values[t]??''));
 return `<h2>АКТ № ${g('АИК.Номер')}</h2><p align="center"><b>входного контроля материалов и изделий</b></p><p>Объект: ${g('Объект.Наименование')}</p><p>Система: ${g('Раздел.Код')}. Дата: ${g('АИК.Дата')}</p><p>Материал: ${g('АИК.Материал')}</p><p>Количество: ${g('АИК.Количество')}</p><p>Документы качества: ${g('Документ.ДокументыКачества')}</p><p>Примечание: ${g('Документ.Примечание')}</p><p>Заключение комиссии: ____________________________________</p><p>Подписи: ____________________________________</p>`;
}
