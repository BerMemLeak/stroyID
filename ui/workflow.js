/* Document workflow: shared certificates, explicit company context and predictable editors. */
function shortFio(value) {
  const parts = String(value || '').trim().split(/\s+/).filter(Boolean);
  return parts.length ? parts[0] + (parts.length > 1 ? ' ' + parts.slice(1).map(p => p.split('-').map(n => Array.from(n)[0] + '.').join('-')).join(' ') : '') : '';
}
const workflowEnsure = ensureWorkspace;
ensureWorkspace = () => {
  workflowEnsure();
  if (!S) return;
  S.lib.quality = S.lib.quality || [];
  S.lib.people.forEach(p => {
    if (p.fio?.trim()) p.fioShort = shortFio(p.fio);
  });
  S.projects.forEach(p => p.systems.forEach(s => resourceList(s).forEach(x => {
    if (x.record.frameEnabled === undefined) x.record.frameEnabled = true;
  })));
};
const workflowGet = getEnt;
getEnt = (ent, id) => ent === 'quality' ? S.lib.quality?.find(d => d.id === id) : workflowGet(ent, id);
const workflowDocs = mDocs;
mDocs = m => {
  const source = baseOf(m) || m;
  if (!source) return [];
  const shared = (source.docIds || []).map(id => S.lib.quality?.find(d => d.id === id)).filter(Boolean);
  return [...new Map([...workflowDocs(m), ...shared].map(d => [d.id, d])).values()];
};

function qualityMaterials() {
  return [...S.lib.base.map(m => ({
    m,
    ent: 'base',
    label: 'Общая база'
  })), ...S.projects.flatMap(p => p.materials.filter(m => !m.baseId).map(m => ({
    m,
    ent: 'mat',
    label: p.name
  })))];
}

function materialOptions(materials, selected = [], multiple = true, scopes = {}) {
  const categories = [...new Set(materials.map(m => mF(m, 'category') || 'Без категории'))].sort();
  return `<div class="material-picker"><div class="g2 mb"><input data-material-search placeholder="Название, производитель или номер документа"><select data-material-category><option value="">Все категории</option>${categories.map(c=>`<option>${esc(c)}</option>`).join('')}</select></div>${multiple?'<div class="row mb"><button type="button" class="btn sm" data-a="materialSelectVisible">Выбрать найденные</button><button type="button" class="btn sm" data-a="materialClearVisible">Снять найденные</button></div>':''}<div class="lst material-results">${materials.map(m=>`<label data-material-row data-category="${esc(mF(m,'category')||'Без категории')}" data-search="${esc(norm([mName(m),mF(m,'maker'),...mDocs(m).map(d=>d.num)].join(' ')))}"><input name="material-choice" type="${multiple?'checkbox':'radio'}" value="${m.id}" ${selected.includes(m.id)?'checked':''}><span class="grow">${esc(mName(m))}<small class="t2">${scopes[m.id]?esc(scopes[m.id])+' · ':''}${esc(mF(m,'category'))} · ${esc(mF(m,'maker'))}</small></span><span class="pill p-n">${mDocs(m).length} док.</span></label>`).join('')}</div><p class="small mut" data-material-empty hidden>По этому запросу материалов нет.</p></div>`;
}

function filterMaterials(el) {
  const box = el.closest('.material-picker');
  if (!box) return;
  const q = norm(box.querySelector('[data-material-search]').value),
    cat = box.querySelector('[data-material-category]').value;
  let count = 0;
  box.querySelectorAll('[data-material-row]').forEach(row => {
    const show = (!q || row.dataset.search.includes(q)) && (!cat || row.dataset.category === cat);
    row.hidden = !show;
    if (show) count++;
  });
  box.querySelector('[data-material-empty]').hidden = !!count;
}
document.addEventListener('input', e => {
  if (e.target.matches('[data-material-search]')) filterMaterials(e.target);
});
document.addEventListener('change', e => {
  if (e.target.matches('[data-material-category]')) filterMaterials(e.target);
});
A.materialSelectVisible = () => document.querySelectorAll('.dlg [data-material-row]:not([hidden]) input:not(:disabled)').forEach(x => x.checked = true);
A.materialClearVisible = () => document.querySelectorAll('.dlg [data-material-row]:not([hidden]) input:not(:disabled)').forEach(x => x.checked = false);

function selectedMaterials() {
  return [...document.querySelectorAll('.dlg .material-results input:checked')].map(x => x.value);
}
A.actMatAdd = d => {
  if (!guard()) return;
  const {
    p,
    s,
    o: a
  } = ctx('act', d.id);
  modal('Материалы для ' + a.num, materialOptions(p.materials, a.materials), [{
    l: 'Отмена'
  }, {
    l: 'Применить',
    c: 'pri',
    f: () => {
      const selected = selectedMaterials();
      a.materials = [...a.materials.filter(id => !p.materials.some(m => m.id === id)), ...selected];
      Object.keys(a.aikLinks).forEach(id => {
        if (!a.materials.includes(id)) delete a.aikLinks[id];
      });
      a.materials.forEach(id => {
        const k = s.aik.find(k => k.materialId === id);
        if (k && !a.aikLinks[id]) a.aikLinks[id] = k.id;
      });
      commit('Изменены материалы ' + a.num, a);
    }
  }], 'wide');
};
A.systemMatPick = d => {
  if (!guard()) return;
  const {
    p,
    o: s
  } = ctx('sys', d.s);
  modal('Материалы системы ' + s.code, materialOptions(p.materials, s.materialIds || []), [{
    l: 'Отмена'
  }, {
    l: 'Применить',
    c: 'pri',
    f: () => {
      s.materialIds = selectedMaterials();
      commit('Выбраны материалы системы ' + s.code, s);
    }
  }], 'wide');
};
A.matFromBase = d => {
  if (!guard()) return;
  const p = proj(d.p),
    have = new Set(p.materials.map(m => m.baseId));
  modal('Добавить из базы паспортов', materialOptions(S.lib.base.filter(m => !have.has(m.id))), [{
    l: 'Отмена'
  }, {
    l: 'Добавить',
    c: 'pri',
    f: () => {
      const ids = selectedMaterials();
      if (!ids.length) {
        toast('Выберите материалы');
        return false;
      }
      ids.forEach(id => p.materials.push({
        id: 'm' + uid(),
        baseId: id,
        name: '',
        category: '',
        brand: '',
        maker: '',
        note: '',
        docs: []
      }));
      commit('Добавлено материалов из базы: ' + ids.length);
    }
  }], 'wide');
};
A.aikMaterialPick = d => {
  const {
    p,
    o: k
  } = ctx('aik', d.id);
  modal('Материал входного контроля', materialOptions(p.materials, [k.materialId], false), [{
    l: 'Отмена'
  }, {
    l: 'Выбрать',
    c: 'pri',
    f: () => {
      const id = selectedMaterials()[0];
      if (!id) return false;
      const el = document.createElement('select');
      el.innerHTML = `<option value="${id}"></option>`;
      Object.assign(el.dataset, {
        ent: 'aik',
        id: k.id,
        f: 'materialId'
      });
      apply(el, false);
      render();
    }
  }], 'wide');
};

docsTable = (m, ed, ent, id) => {
  if (!m) return '';
  const source = baseOf(m) || m,
    actualEnt = m.baseId ? 'base' : ent,
    actualId = source.id,
    docs = mDocs(m);
  return `<div class="tw"><table class="tbl"><thead><tr><th>Документ</th><th>Начало</th><th>Окончание</th><th>Файл</th>${ed?'<th></th>':''}</tr></thead><tbody>${docs.map(d=>`<tr><td>${esc(d.type)} № ${esc(d.num||'—')}<div class="t2">${S.lib.quality.some(q=>q.id===d.id)?'Общий документ · '+qualityMaterials().filter(x=>x.m.docIds?.includes(d.id)).length+' материалов':''}</div></td><td>${fmtD(d.validFrom??d.date??'')||'—'}</td><td>${fmtD(d.validTo||'')||'—'}</td><td>${d.fileKey?B(esc(d.file||'Открыть'),'openBlob',`data-key="${esc(d.fileKey)}"`,'sm'):esc(d.file||'Нет файла')}</td>${ed?`<td>${B('Изменить / материалы','qualityEdit',`data-ent="${actualEnt}" data-id="${actualId}" data-q="${d.id}"`,'sm')}${B('Отвязать','qualityUnlink',`data-ent="${actualEnt}" data-id="${actualId}" data-q="${d.id}"`,'sm ghost')}</td>`:''}</tr>`).join('')}</tbody></table></div>${ed?`<div class="row mt">${B('Добавить документ','qualityEdit',`data-ent="${actualEnt}" data-id="${actualId}"`)}${B('Выбрать существующий','qualityChoose',`data-ent="${actualEnt}" data-id="${actualId}"`)}</div>`:''}`;
};
let qualityDraft = null;
A.qualityEdit = d => {
  if (!guard()) return;
  const m = getEnt(d.ent, d.id),
    old = mDocs(m).find(q => q.id === d.q),
    shared = S.lib.quality.find(q => q.id === d.q),
    draft = structuredClone(old || {
      id: 'q' + uid(),
      type: QDOC[0],
      num: '',
      date: '',
      file: '',
      pages: 0
    });
  qualityDraft = draft;
  const materials = qualityMaterials(),
    selected = materials.filter(x => x.m.id === m.id || x.m.docIds?.includes(draft.id)).map(x => x.m.id);
  modal(old ? 'Изменить документ качества' : 'Новый документ качества', `<div class="g2"><label class="fld"><span>Тип</span><select id="quality-type">${QDOC.map(t=>`<option ${t===draft.type?'selected':''}>${esc(t)}</option>`).join('')}</select></label><label class="fld"><span>Номер</span><input id="quality-num" value="${esc(draft.num)}"></label><label class="fld"><span>Начало действия</span><input type="date" id="quality-from" value="${esc(draft.validFrom??draft.date??'')}"></label><label class="fld"><span>Окончание действия</span><input type="date" id="quality-to" value="${esc(draft.validTo||'')}"></label></div><p class="small mut">Даты можно оставить пустыми. Изменения документа применяются ко всем выбранным материалам.</p><div class="row mb"><span id="quality-file">${esc(draft.file||'Файл не выбран')}</span>${B('Загрузить файл','qualityFile')}</div><h3>Материалы документа</h3>${materialOptions(materials.map(x=>x.m),selected,true,Object.fromEntries(materials.map(x=>[x.m.id,x.label])))}`, [{
    l: 'Отмена',
    f: () => {
      qualityDraft = null;
    }
  }, {
    l: 'Сохранить',
    c: 'pri',
    f: () => {
      const from = $('#quality-from').value,
        to = $('#quality-to').value,
        ids = selectedMaterials();
      if (from && to && to < from) {
        toast('Окончание не может быть раньше начала');
        return false;
      }
      if (!ids.length) {
        toast('Выберите хотя бы один материал');
        return false;
      }
      Object.assign(draft, {
        type: $('#quality-type').value,
        num: $('#quality-num').value.trim(),
        validFrom: from,
        validTo: to,
        date: from
      });
      if (shared) Object.assign(shared, draft);
      else S.lib.quality.push(draft);
      materials.forEach(x => {
        x.m.docIds = (x.m.docIds || []).filter(id => id !== draft.id);
        if (ids.includes(x.m.id)) x.m.docIds.push(draft.id);
      });
      if (old && !shared) m.docs = m.docs.filter(q => q.id !== old.id);
      qualityDraft = null;
      commit('Сохранён общий документ качества ' + draft.num);
    }
  }], 'wide');
};
A.qualityFile = async () => {
  const draft = qualityDraft;
  try {
    const f = await nativeCall('pickAny');
    if (f && draft === qualityDraft && $('#quality-file')) {
      Object.assign(draft, {
        file: f.name,
        fileKey: f.id,
        pages: f.pages
      });
      $('#quality-file').textContent = f.name;
    }
  } catch (e) {
    toast(e.message);
  }
};
A.qualityChoose = d => {
  if (!guard()) return;
  const m = getEnt(d.ent, d.id),
    docs = S.lib.quality;
  modal('Общие документы качества', `<input placeholder="Номер или тип документа" id="quality-search"><div class="lst mt">${docs.map(q=>`<label data-quality-search="${esc(norm(q.type+' '+q.num))}"><input type="checkbox" value="${q.id}" ${m.docIds?.includes(q.id)?'checked':''}><span>${esc(q.type+' № '+q.num)} · ${esc(q.file||'Нет файла')}</span></label>`).join('')||'Общих документов пока нет. Добавьте документ и выберите его материалы.'}</div>`, [{
    l: 'Отмена'
  }, {
    l: 'Применить',
    c: 'pri',
    f: () => {
      m.docIds = [...document.querySelectorAll('.dlg [data-quality-search] input:checked')].map(x => x.value);
      commit('Изменены связи документов материала');
    }
  }], 'wide');
};
document.addEventListener('input', e => {
  if (e.target.id === 'quality-search') document.querySelectorAll('[data-quality-search]').forEach(x => x.hidden = !x.dataset.qualitySearch.includes(norm(e.target.value)));
});
A.qualityUnlink = d => {
  if (!guard()) return;
  const m = getEnt(d.ent, d.id);
  if (S.lib.quality.some(q => q.id === d.q)) {
    m.docIds = (m.docIds || []).filter(id => id !== d.q);
    commit('Документ отвязан от материала');
    toast('Связь удалена. Документ можно выбрать повторно.');
  } else A.rowRm({
    ent: d.ent,
    id: d.id,
    p: 'docs',
    r: d.q
  });
};

// A scheme is created only after the user confirms its name and a real PDF.
let schemeDraft = null;
A.sketchAdd = d => {
  if (!guard()) return;
  const s = getEnt('sys', d.s);
  schemeDraft = {
    ...ROWT.scheme(s),
    frameEnabled: true
  };
  modal('Новая исполнительная схема', `<label class="fld"><span>Наименование</span><input id="scheme-draft-name" value="Исполнительная схема"></label><p id="scheme-draft-file">PDF не выбран</p>${B('Выбрать PDF','schemeDraftFile')}`, [{
    l: 'Отмена',
    f: () => {
      schemeDraft = null;
    }
  }, {
    l: 'Создать',
    c: 'pri',
    f: () => {
      const x = schemeDraft,
        name = $('#scheme-draft-name').value.trim();
      if (!name || !x?.fileKey) {
        toast('Укажите наименование и выберите PDF');
        return false;
      }
      x.name = name;
      (d.a ? getEnt('act', d.a).schemes : s.sketches).push(x);
      schemeDraft = null;
      commit('Добавлена схема ' + name, s);
    }
  }]);
};
A.schemeDraftFile = async () => {
  const draft = schemeDraft;
  try {
    const f = await nativeCall('pickPdf');
    if (f && draft === schemeDraft && $('#scheme-draft-file')) {
      Object.assign(draft, {
        file: f.name,
        fileKey: f.id,
        pages: f.pages
      });
      $('#scheme-draft-file').textContent = f.name;
    }
  } catch (e) {
    toast(e.message);
  }
};

function schemeActs(s, x) {
  return s.acts.filter(a => a.id === x.owner?.id || a.schemeLinks.some(l => l.id === x.id));
}
schemeCatalog = (p, s) => `<div class="catalog-top"><p>Схемы необязательны. Добавляйте исходные PDF и связи с актами при необходимости.</p>${B('Добавить схему','sketchAdd',`data-s="${s.id}"`,'pri')}</div><div class="file-grid">${resourceList(s).map(x=>{const used=schemeActs(s,x);return `<div class="resource"><span class="sectionlabel">${x.kind==='system'?'Комплект системы':x.kind==='act'?'Схема из акта '+esc(x.owner.num):'Отдельная схема'}</span><h3>${esc(x.name)}</h3><p>${esc(x.record.file||'Файл не загружен')}</p><p class="small">${x.record.pages||0} л. · ${used.length} связей с актами</p><p>${used.map(a=>`<a href="#/a/${a.id}/schemes">${esc(a.num)}</a>`).join(' · ')}</p><div class="row">${B('Предпросмотр','drawingEdit',`data-s="${s.id}" data-x="${x.id}"`,'sm')}${x.kind==='system'?B(x.record.file?'Заменить PDF':'Загрузить PDF','schemeFile',`data-s="${s.id}"`,'sm'):x.kind==='extra'?B('Карточка','sketchEdit',`data-s="${s.id}" data-x="${x.id}"`,'sm')+B('Заменить PDF','pickPdf',`data-ent="sys" data-id="${s.id}" data-p="sketches.#${x.id}"`,'sm'):B('Открыть в акте','nav',`data-h="#/a/${x.owner.id}/schemes"`,'sm')}${x.kind!=='system'?B('Удалить','schemeDelete',`data-s="${s.id}" data-x="${x.id}"`,'sm dng'):''}</div></div>`;}).join('')}</div>`;
A.schemeDelete = d => {
  const s = getEnt('sys', d.s),
    x = drawingRecord(s, d.x);
  if (!x || x.kind === 'system') return;
  const used = schemeActs(s, x);
  confirmBox('Удалить схему', `Схема будет перенесена в корзину.${used.length?' Она используется в актах: '+used.map(a=>esc(a.num)).join(', ')+'. Связи сохранятся для восстановления.':''}`, () => folderMutation('trashMove', x.kind === 'act' ? {
    ent: 'act',
    id: x.owner.id,
    path: 'schemes',
    row: x.id
  } : {
    ent: 'sys',
    id: s.id,
    path: 'sketches',
    row: x.id
  }));
};
const workflowDrawingPanel = drawingPanel;
drawingPanel = (p, s, item) => {
  const box = document.createElement('div');
  box.innerHTML = workflowDrawingPanel(p, s, item);
  box.querySelectorAll('[data-a="drawingTemplateSave"],[data-a="drawingTemplatePick"],[data-a="drawingTemplateReset"]').forEach(b => b.closest('.row')?.remove());
  box.querySelectorAll('p').forEach(p => { if (p.textContent.includes('Теги:')) p.remove(); });
  return box.innerHTML;
};
const workflowDrawingEdit = A.drawingEdit;
A.drawingEdit = d => {
  workflowDrawingEdit(d);
  if (drawingRecord(getEnt('sys', d.s), d.x)?.record.fileKey) A.drawingPreview(d);
};
const workflowDrawingContext = drawingContext;
drawingContext = (p, s, item, vol, owner = null) => {
  const effective = exportCompanyProject(p),
    r = workflowDrawingContext(effective, s, item, vol, owner),
    pf = exportProfile(p) || prof(vol?.sp?.profileId);
  r.templateKey = pf?.frameTemplate?.fileKey || p.frameTemplate?.fileKey || r.templateKey;
  if (org(p.exportIssuer)) r.values['Комплект.Компания.Наименование'] = org(p.exportIssuer).full || org(p.exportIssuer).short;
  r.requireFont = true;
  r.fontKey = S.meta.drawingFont?.fileKey || '';
  return r;
};

// Template selection belongs to the profile/object, not each drawing card.
const workflowWordSection = wordSectionBody;
wordSectionBody = (section, p, profile, map) => {
  if (['orders', 'quality', 'pass'].includes(section[0])) return '';
  if (section[0] !== 'schemes') {
    const html = workflowWordSection(section, p, profile, map);
    return ['title', 'reg'].includes(section[0]) ? html + B('Добавить образец', 'referenceTemplate', `data-section="${section[0]}"`, 'sm mb') : html;
  }
  const owner = profile || p;
  if (!owner) return '<div class="card">Создайте объект или профиль для выбора рамки.</div>';
  return `<div class="card"><h3>Исполнительные схемы — HTML-рамка</h3><p>${esc(owner.frameTemplate?.file||'Встроенная рамка ГОСТ Р 21.101-2026')}</p><div class="row">${B('Загрузить HTML','frameProfilePick',`data-ent="${profile?'pf':'proj'}" data-id="${owner.id}"`,'pri')}${B('Скачать образец','drawingTemplateSave')}${owner.frameTemplate?B('Вернуть встроенную','frameProfileReset',`data-ent="${profile?'pf':'proj'}" data-id="${owner.id}"`):''}</div><p>${B('Проверить ISOCPEUR','frameFontStatus')}${B('Загрузить шрифт','frameFontPick')}</p><p class="small mut">Предпросмотр и включение рамки доступны в карточке схемы. Для новой схемы рамка включена.</p></div>`;
};
A.frameProfilePick = async d => {
  if (!guard()) return;
  try {
    const f = await nativeCall('pickFrameTemplate');
    if (f) {
      getEnt(d.ent, d.id).frameTemplate = {
        file: f.name,
        fileKey: f.id
      };
      commit('Выбран HTML-шаблон рамки');
    }
  } catch (e) {
    toast(e.message);
  }
};
A.frameProfileReset = d => {
  if (!guard()) return;
  delete getEnt(d.ent, d.id).frameTemplate;
  commit('Возвращена встроенная рамка');
};

// Issuer and recipient belong to the package, not to construction roles.
function exportCompanyProject(p) { return p; }
const workflowAssemblyRules = assemblyRules;
assemblyRules = (p, plan) => {
  const cfg = assemblyPick(p);
  plan.volumes = plan.volumes.filter(v => (cfg.includeCommon !== false || v.kind !== 'T1') && (cfg.includeOperations !== false || v.kind !== 'T3'));
  for (const v of plan.volumes) {
    const seen = new Set();
    v.documents = v.documents.filter(d => {
      if (!d.qualityId) return true;
      if (seen.has(d.id)) return false;
      seen.add(d.id);
      return true;
    });
  }
  return workflowAssemblyRules(p, plan);
};
const workflowBuild = V.build;
V.build = r => {
  const p = proj(r[1]) || S.projects[0];
  if (!p) return workflowBuild(r);
  const c = assemblyPick(p),
    box = document.createElement('div');
  box.innerHTML = workflowBuild(r);
  const opts = [
    ['', 'Не выбрана'], ...S.lib.orgs.map(o => [o.id, o.short || o.full])
  ];
  box.querySelector('.page > .card')?.insertAdjacentHTML('beforeend', `<div class="g2 mt">${F('Компания выпуска комплекта','proj',p.id,'exportIssuer',p.exportIssuer||'',{opts,rr:1})}${F('Получатель комплекта','proj',p.id,'exportCustomer',p.exportCustomer||'',{opts,rr:1})}</div><div class="row mt"><label><input type="checkbox" data-assembly="includeCommon" data-p="${p.id}" ${c.includeCommon!==false?'checked':''}> Общая документация</label><label><input type="checkbox" data-assembly="includeOperations" data-p="${p.id}" ${c.includeOperations!==false?'checked':''}> ИД для эксплуатации</label></div>`);
  return box.innerHTML;
};
document.addEventListener('change', e => {
  if (!['includeCommon', 'includeOperations'].includes(e.target.dataset.assembly)) return;
  e.stopImmediatePropagation();
  assemblyPick(proj(e.target.dataset.p))[e.target.dataset.assembly] = e.target.checked;
  render();
}, true);

// Expand any execution independently of the currently selected page.
const workflowTree = renderTree;
renderTree = () => {
  workflowTree();
  const p = curProject();
  if (!p) return;
  S.ui.expandedExecutions = S.ui.expandedExecutions || {};
  document.querySelectorAll('#tree a[href^="#/e/"]').forEach(link => {
    const eid = link.getAttribute('href').split('/')[3],
      e = execution(p, eid),
      row = link.closest('.tn');
    if (!e) return;
    const adjacent = row.nextElementSibling,
      isBranch = adjacent?.classList.contains('navbranch'),
      open = S.ui.expandedExecutions[eid] ?? isBranch;
    row.insertAdjacentHTML('afterbegin', B(open ? '▾' : '▸', 'executionExpand', `data-id="${eid}" aria-label="${open?'Свернуть':'Раскрыть'} ${esc(e.name)}" aria-expanded="${open}"`, 'sm icon ghost'));
    if (isBranch) adjacent.remove();
    if (open) row.insertAdjacentHTML('afterend', `<div class="navbranch">${p.systems.filter(s=>s.executionId===eid).map(s=>`<div class="tn"><a href="#/s/${s.id}">${esc(s.code+' · '+s.name)}</a></div>`).join('')||'<div class="small mut">Систем пока нет</div>'}</div>`);
  });
};
A.executionExpand = d => {
  const row = document.querySelector('#tree [data-a="executionExpand"][data-id="' + CSS.escape(d.id) + '"]');
  S.ui.expandedExecutions[d.id] = row?.getAttribute('aria-expanded') !== 'true';
  renderTree();
};

// Shared project attachments have one dedicated card in General sections.
const workflowProject = V.p;
V.p = r => {
  const p = proj(r[1]);
  if (!p) return workflowProject(r);
  if (r[2] === 'additional') return `<div class="page">${hdr('Дополнительные документы',esc(p.name),'',`<a href="#/p/${p.id}/general">Общие разделы</a>`)}<div class="card">${(p.attachments||[]).map(f=>`<p>${B(esc(f.name||f.file),'openBlob',`data-key="${esc(f.fileKey)}"`)}</p>`).join('')||'Документов пока нет.'}${B('Добавить файл','additionalAdd',`data-id="${p.id}"`)}</div></div>`;
  const box = document.createElement('div');
  box.innerHTML = workflowProject(r);
  if (r[2] === 'general') box.querySelector('.section-grid')?.insertAdjacentHTML('beforeend', tile('#/p/' + p.id + '/additional', 'Дополнительные документы', 'Прочие файлы объекта', (p.attachments || []).length + ' документов', 'folder'));
  return box.innerHTML;
};

const workflowRender = render;
render = () => {
  workflowRender();
  document.querySelectorAll('#content .tabs').forEach(x => x.classList.add('system-tabs'));
  document.querySelectorAll('#content [data-ent="per"][data-f="fioShort"]').forEach(x => x.closest('label')?.remove());
  document.querySelectorAll('#content .ph [data-a="desktopSave"]').forEach(x => x.remove());
  const r = route();
  if (r[0] === 's') {
    document.querySelectorAll('#content .ph [data-a="del"][data-ent="sys"],#content .ph [data-a="newAct"]').forEach(x => x.remove());
  }
  if (r[0] === 'p' && r[2] !== 'additional') {
    document.querySelectorAll('#content .card').forEach(c => {
      if (c.querySelector('h3')?.textContent.trim() === 'Дополнительные документы') c.remove();
    });
  }
  document.querySelectorAll('#content select[data-ent="aik"][data-f="materialId"]').forEach(el => {
    if (!el.parentElement.querySelector('[data-a="aikMaterialPick"]')) el.insertAdjacentHTML('afterend', B('Найти материал', 'aikMaterialPick', `data-id="${el.dataset.id}"`, 'sm'));
  });
  installExportDrag();
};

// Drag handles, with keyboard reordering for accessibility.
let exportDrag = null;

function installExportDrag() {
  for (const action of ['profileMove', 'assemblyMove', 'assemblyDocMove', 'blkMv', 'docMv']) document.querySelectorAll('#content [data-a="' + action + '"]').forEach(button => {
    const row = button.closest('.row');
    if (!row) return;
    if (row.dataset.sortAction) {
      button.remove();
      return;
    }
    const d = {
      ...button.dataset
    };
    row.dataset.sortAction = action;
    row.dataset.sortData = JSON.stringify(d);
    const locked = action !== 'profileMove' && proj(d.p)?.exportMode === 'profile';
    row.draggable = !locked;
    row.classList.add('export-sort-row');
    const handle = document.createElement('button');
    handle.type = 'button';
    handle.className = 'btn sm drag-handle';
    handle.textContent = '⠿';
    handle.disabled = locked;
    handle.title = 'Перетащите; Alt + стрелка вверх/вниз';
    handle.setAttribute('aria-label', 'Изменить порядок');
    row.prepend(handle);
    button.remove();
  });
}

function exportSortGroup(row) {
  const d = JSON.parse(row.dataset.sortData);
  return [row.dataset.sortAction, d.p || '', d.v || '', row.dataset.sortAction === 'profileMove' ? d.id : row.dataset.sortAction === 'assemblyDocMove' ? d.k : ''].join('|');
}

function reorderExport(from, to) {
  if (!guard() || !from || !to || from === to || exportSortGroup(from) !== exportSortGroup(to)) return;
  const a = JSON.parse(from.dataset.sortData),
    b = JSON.parse(to.dataset.sortData),
    action = from.dataset.sortAction;
  let list, source, target;
  if (action === 'profileMove') {
    list = prof(a.id).exportSettings.order;
    source = a.key;
    target = b.key;
  } else if (['assemblyMove', 'assemblyDocMove'].includes(action)) {
    const p = proj(a.p);
    if (p.exportMode === 'profile') return;
    const v = volumeList(p).find(v => v.key === a.v),
      cfg = S.volCfg[a.p + '|' + a.v] = S.volCfg[a.p + '|' + a.v] || {};
    if (action === 'assemblyMove') {
      list = cfg.order = cfg.order || blocksFor(p, v).map(x => x.key);
      source = a.k;
      target = b.k;
    } else {
      cfg.docs = cfg.docs || {};
      list = cfg.docs[a.k] = cfg.docs[a.k] || blocksFor(p, v).find(x => x.key === a.k).items.map(x => x.id);
      source = a.id;
      target = b.id;
    }
  } else return;
  const i = list.indexOf(source),
    j = list.indexOf(target);
  if (i < 0 || j < 0) return;
  list.splice(i, 1);
  list.splice(j, 0, source);
  commit('Изменён порядок экспорта');
}
document.addEventListener('dragstart', e => {
  const row = e.target.closest('.export-sort-row');
  if (!row || !row.draggable) return;
  exportDrag = row;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', row.dataset.sortData);
  row.classList.add('dragging');
});
document.addEventListener('dragover', e => {
  const row = e.target.closest('.export-sort-row');
  if (exportDrag && row && exportSortGroup(exportDrag) === exportSortGroup(row)) {
    e.preventDefault();
    document.querySelectorAll('.drop-target').forEach(x => x.classList.remove('drop-target'));
    row.classList.add('drop-target');
  }
});
document.addEventListener('drop', e => {
  const row = e.target.closest('.export-sort-row');
  if (exportDrag && row) {
    e.preventDefault();
    reorderExport(exportDrag, row);
  }
  exportDrag = null;
});
document.addEventListener('dragend', () => {
  exportDrag = null;
  document.querySelectorAll('.dragging,.drop-target').forEach(x => x.classList.remove('dragging', 'drop-target'));
});
document.addEventListener('keydown', e => {
  if (!e.altKey || !['ArrowUp', 'ArrowDown'].includes(e.key) || !e.target.matches('.drag-handle')) return;
  e.preventDefault();
  const row = e.target.closest('.export-sort-row'),
    rows = [...document.querySelectorAll('.export-sort-row')].filter(x => exportSortGroup(x) === exportSortGroup(row)),
    i = rows.indexOf(row);
  reorderExport(row, rows[i + (e.key === 'ArrowUp' ? -1 : 1)]);
});

A.frameFontStatus = async () => {
  try {
    const r = await nativeCall('frameFontStatus', {
      key: S.meta.drawingFont?.fileKey || ''
    });
    toast(r.available ? 'ISOCPEUR доступен' : 'ISOCPEUR не найден. Выберите файл шрифта кнопкой «Загрузить шрифт».');
  } catch (e) {
    toast(e.message);
  }
};
A.frameFontPick = async () => {
  if (!guard()) return;
  try {
    const f = await nativeCall('pickFrameFont');
    if (f) {
      S.meta.drawingFont = {
        file: f.name,
        fileKey: f.id
      };
      commit('Загружен шрифт рамки ISOCPEUR');
    }
  } catch (e) {
    toast(e.message);
  }
};
A.additionalAdd = async d => {
  if (!guard()) return;
  try {
    const f = await nativeCall('pickAny');
    if (f) {
      const p = proj(d.id);
      p.attachments = p.attachments || [];
      p.attachments.push({
        id: uid(),
        name: f.name,
        file: f.name,
        fileKey: f.id,
        pages: f.pages
      });
      commit('Добавлен дополнительный документ');
    }
  } catch (e) {
    toast(e.message);
  }
};

A.referenceTemplate = async d => {
  if (!guard()) return;
  try {
    const f = await nativeCall('referenceTemplate', {
      section: d.section
    });
    const t = {
      id: 'tpl' + uid(),
      name: d.section === 'title' ? 'Титульный лист — образец' : 'Реестр — образец',
      section: d.section,
      type: d.section === 'title' ? 'Титульный лист' : 'Реестр',
      file: f.name,
      fileKey: f.id,
      tags: f.tags
    };
    S.lib.templates.push(t);
    const c = wordUIContext();
    if (c.map) c.map[d.section] = t.id;
    commit('Добавлен шаблон ' + t.name);
  } catch (e) {
    toast(e.message);
  }
};

const workflowRowAdd = A.rowAdd;
A.rowAdd = d => {
  if (d.ent === 'act' && d.p === 'schemes' && d.k === 'scheme') {
    const c = ctx('act', d.id);
    return A.sketchAdd({
      s: c.s.id,
      a: d.id
    });
  }
  return workflowRowAdd(d);
};
const workflowActSchemes = actSchemes;
actSchemes = (a, s) => {
  const box = document.createElement('div');
  box.innerHTML = workflowActSchemes(a, s);
  box.querySelectorAll('[data-a="ownPrev"]').forEach(b => b.textContent = 'Предпросмотр');
  box.querySelectorAll('.sheet-link').forEach((row, i) => {
    const linked = linkedSchemes(a, s)[i];
    if (linked?.item) row.insertAdjacentHTML('beforeend', B('Предпросмотр', 'drawingEdit', `data-s="${s.id}" data-x="${linked.item.id}"`, 'sm'));
  });
  return box.innerHTML;
};

// The built-in title has the same company logo behavior as DOCX templates.
const workflowPdfTitle = pdfTitle;
pdfTitle = (p, vol) => (p.logo ? `<p align="right"><img src="${esc(p.logo)}" width="150"></p>` : '') + workflowPdfTitle(p, vol);
