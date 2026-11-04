/* ===================== ДЕЙСТВИЯ ===================== */
const A = {};
A.nav = (d) => {
  if (d.h) go(d.h);
};
A.stub = (d) => toast((d.t || "Функция") + " — заглушка прототипа");
A.tw = (d) => {
  S.ui.exp[d.k] = !S.ui.exp[d.k];
  save();
  renderTree();
};
A.setUi = (d) => {
  S.ui.f[d.k] = d.v;
  save();
  render();
};
A.doSearch = () => {
  const q = $("#gsearch").value.trim();
  S.ui.q = q;
  save();
  go("#/search/" + encodeURIComponent(q));
};
A.menu = (d, el) => {
  if ($("#mimenu")) {
    closeMenu();
    return;
  }
  const p = curProject();
  const m = document.createElement("div");
  m.id = "mimenu";
  m.className = "mi-menu";
  const rk = routeKey();
  const ra = route()[0] === "a";
  m.innerHTML = `${rk ? `<div class="mh">Совместная работа (имитация)</div><a href="#" data-a="simLock">Коллега взял ${esc(lockName(rk))} одновременно</a><a href="#" data-a="simStale">Брошенная метка коллеги</a>${ra ? '<a href="#" data-a="simChange">Коллега изменил этот акт</a><a href="#" data-a="simConflict">Конфликт версий при сохранении</a>' : ""}<hr>` : ""}${p ? `<a href="#/p/${p.id}/check">Проверка объекта</a>` : ""}<a href="#/settings/trash">Корзина${S.trash.length ? " (" + S.trash.length + ")" : ""}</a><hr><a href="#/import">Импорт документов</a><a href="#/files">Папка базы</a><a href="#" data-a="baseSwitch">Сменить базу</a><hr><a href="#" data-a="roToggle">${S.ui.ro ? "Включить редактирование" : "Режим только просмотра"}</a><a href="#/settings">Настройки</a>`;
  document.body.appendChild(m);
};
A.roToggle = () => {
  S.ui.ro = !S.ui.ro;
  logH(S.ui.ro ? "Включён режим только просмотра" : "Включено редактирование");
  save();
  render();
};

/* --- создание --- */
A.newProject = () => {
  if (!guard(null)) return;
  modal(
    "Новый объект",
    `<div style="display:grid;gap:12px"><label class="fld"><span>Полное наименование объекта <b class="req">*</b></span><input id="np-n" placeholder="Например: Жилой дом, корпус 3"></label><div class="g2"><label class="fld"><span>Шифр проекта</span><input id="np-c"></label></div><label class="fld"><span>Адрес</span><input id="np-a"></label></div>`,
    [
      { l: "Отмена" },
      {
        l: "Создать",
        c: "pri",
        f: () => {
          const n = $("#np-n").value.trim();
          if (!n) {
            toast("Укажите наименование");
            return false;
          }
          const p = {
            id: "P" + uid(),
            name: n,
            address: $("#np-a").value.trim(),
            cipher: $("#np-c").value.trim(),
            genContractor: "",
            developer: "",
            techCustomer: "",
            designOrg: "",
            supervision: "",
            operator: "",
            contract: "",
            startDate: "",
            logo: "",
            extra: [],
            materials: [],
            systems: [],
            journals: [],
            surveys: [],
            opsDocs: [],
            remarks: [],
          };
          S.projects.push(p);
          S.ui.exp[p.id] = true;
          logH("Создан объект «" + p.name + "»");
          save();
          closeModal();
          go("#/p/" + p.id);
        },
      },
    ],
  );
};
A.newSystem = (d) => {
  const p = proj(d.p) || curProject();
  if (!p || !guard("obj:" + p.id)) return;
  const used = new Set(p.systems.map((s) => s.code));
  modal(
    "Новая система — " + p.name,
    `<div class="small mut mb">Выберите из справочника или задайте свою.</div><div class="lst" style="max-height:300px">${SYS_CATALOG.map(([c, n]) => `<label><input type="radio" name="ns" value="${c}" ${used.has(c) ? "disabled" : ""}><b style="width:56px">${c}</b><span class="grow">${esc(n)}</span>${used.has(c) ? '<span class="pill p-n">уже есть</span>' : ""}</label>`).join("")}<label><input type="radio" name="ns" value="__own"><span class="grow">Своя система</span></label></div>
 <div class="g2 mt"><label class="fld"><span>Код (для своей)</span><input id="ns-c" placeholder="Например, ВПТ"></label><label class="fld"><span>Наименование (для своей)</span><input id="ns-n"></label></div>`,
    [
      { l: "Отмена" },
      {
        l: "Добавить",
        c: "pri",
        f: () => {
          const r = document.querySelector("input[name=ns]:checked");
          if (!r) {
            toast("Выберите систему");
            return false;
          }
          let code, name;
          if (r.value === "__own") {
            code = $("#ns-c").value.trim();
            name = $("#ns-n").value.trim();
            if (!code || !name) {
              toast("Укажите код и наименование");
              return false;
            }
          } else {
            [code, name] = SYS_CATALOG.find((x) => x[0] === r.value);
          }
          const ref = p.systems[0]?.subprofiles[0];
          const id = "s" + uid();
          const cipher = (p.cipher ? p.cipher + "-" : "") + code;
          const s = {
            id,
            code,
            name,
            cipher,
            order: p.systems.length + 1,
            subprofiles: [
              {
                id: "sp" + uid(),
                name: code + " — основной",
                profileId: ref?.profileId || S.lib.profiles[0]?.id || "",
                execId: ref?.execId || "",
                signers: { ...(ref?.signers || {}) },
              },
            ],
            scheme: {
              file: "",
              pages: 0,
              format: "A3",
              orient: "Альбомная",
              rd: cipher,
              tol: "в пределах допусков СП 70.13330.2012",
              execId: ref?.execId || "",
              pos: "Правый верхний угол",
              mx: 70,
              my: 5,
              allPages: true,
              stamped: false,
              updated: "",
              updatedBy: "",
            },
            acts: [],
            aik: [],
            journals: [],
          };
          p.systems.push(s);
          S.ui.exp[p.id] = true;
          S.ui.exp[id] = true;
          logH(`Добавлена система ${code} в «${p.name}»`);
          save();
          closeModal();
          go("#/s/" + id);
        },
      },
    ],
  );
};
function newActObj(s, src) {
  const last = s.acts.filter((a) => a.type === "АОСР").slice(-1)[0];
  const t = today();
  return {
    id: "a" + uid(),
    type: "АОСР",
    num: nextNum(s, "АОСР"),
    date: t,
    works: src?.works || "",
    place: src?.place || "",
    start: t,
    end: t,
    rd: src?.rd || last?.rd || s.cipher,
    norms: src?.norms || last?.norms || "",
    next: src?.next || "",
    materials: src ? src.materials.slice() : [],
    aikLinks: src ? { ...src.aikLinks } : {},
    subs: src ? src.subs.slice() : s.subprofiles.map((x) => x.id),
    signers: src ? { ...src.signers } : {},
    schemes: [],
    tests: [],
    photos: [],
    scan: { file: "", pages: 0 },
    photoLayout: 2,
    note: "",
    status: "В работе",
    remarks: [],
    updated: nowStr(),
    updatedBy: APP.user,
  };
}
A.newAct = (d) => {
  if (!guard("sys:" + d.s)) return;
  const c = ctx("sys", d.s);
  if (!c.o) return;
  const a = newActObj(c.o);
  c.o.acts.push(a);
  S.ui.exp[c.p.id] = true;
  S.ui.exp[c.o.id] = true;
  logH(`Создан ${a.num} (${c.o.code})`);
  save();
  go("#/a/" + a.id);
};
A.dup = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const c = ctx("act", d.id);
  const a = newActObj(c.s, c.o);
  a.type = c.o.type;
  a.num = nextNum(c.s, a.type);
  c.s.acts.push(a);
  logH(`Дублирован ${c.o.num} → ${a.num}`);
  save();
  toast(`Создан ${a.num}: копия без фото, схем и испытаний`);
  go("#/a/" + a.id);
};
A.newAik = (d) => {
  if (!guard("sys:" + d.s)) return;
  const c = ctx("sys", d.s);
  const p = c.p;
  if (!p.materials.length) {
    toast("Сначала добавьте материалы в объект");
    return go("#/p/" + p.id + "/mats");
  }
  modal(
    "Новый АИК — " + c.o.code,
    `<div class="small mut mb">Выберите материал объекта</div><div class="lst">${p.materials.map((m) => `<label><input type="radio" name="nk" value="${m.id}"><span class="grow">${esc(mName(m))}</span><span class="pill p-n">${mDocs(m).length} док.</span></label>`).join("")}</div>`,
    [
      { l: "Отмена" },
      {
        l: "Создать",
        c: "pri",
        f: () => {
          const r = document.querySelector("input[name=nk]:checked");
          if (!r) {
            toast("Выберите материал");
            return false;
          }
          const k = mkAik(c.o, r.value);
          save();
          closeModal();
          go("#/k/" + k.id);
        },
      },
    ],
  );
};
function mkAik(s, mid) {
  const k = {
    id: "k" + uid(),
    num: nextNum(s, "АИК"),
    date: today(),
    materialId: mid,
    qty: "",
    status: "В работе",
    note: "",
    remarks: [],
    updated: nowStr(),
    updatedBy: S.ui.user,
  };
  s.aik.push(k);
  logH(`Создан ${k.num} (${s.code})`);
  return k;
}
A.aikCreate = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const c = ctx("act", d.id);
  const k = mkAik(c.s, d.m);
  c.o.aikLinks[d.m] = k.id;
  commit("", c.o);
  toast(`Создан ${k.num} и привязан к ${c.o.num}`);
};
A.aikPrev = (d) => {
  const c = ctx("aik", d.id);
  const k = c.o,
    m = pMat(c.p, k.materialId);
  modal(
    "Предпросмотр " + k.num,
    `<div class="paper" style="width:auto"><h2>АКТ № ${esc(k.num)}</h2><div class="c"><b>входного контроля материалов и изделий</b></div><div style="margin:10px 0">Объект: ${esc(c.p.name)}. Система: ${esc(c.s.code)}. Дата: ${fmtD(k.date)}</div><div>Материал: ${pl(esc(mName(m)))}</div><div>Количество: ${pl(esc(k.qty) || "—")}</div><div>Документы качества: ${pl(
      mDocs(m)
        .map((x) => esc(x.type + " № " + x.num + " от " + fmtD(x.date)))
        .join("; "),
    )}</div><div>Заключение: материал соответствует требованиям проектной документации.</div></div>`,
    [{ l: "Закрыть" }],
    "wide",
  );
};
A.newJournal = (d) => {
  if (!guard(d.s ? "sys:" + d.s : "obj:" + d.p)) return;
  const s = d.s ? ctx("sys", d.s).o : null;
  const p = s ? ctx("sys", d.s).p : proj(d.p);
  const kinds = Object.keys(JKINDS).filter((k) =>
    s ? !k.startsWith("Общий") : true,
  );
  modal(
    "Новый журнал",
    `<label class="fld"><span>Вид журнала</span><select id="nj-k">${kinds.map((k) => `<option>${esc(k)}</option>`).join("")}</select></label><label class="fld mt"><span>Наименование</span><input id="nj-n" placeholder="Например: Журнал сварочных работ № 2"></label>`,
    [
      { l: "Отмена" },
      {
        l: "Создать",
        c: "pri",
        f: () => {
          const kind = $("#nj-k").value;
          const nn =
            (s || p).journals.filter((x) => x.kind === kind).length + 1;
          const j = {
            id: "j" + uid(),
            name:
              $("#nj-n").value.trim() ||
              kind.replace(" (ОЖР)", "").replace(" (конструктор)", "") +
                " № " +
                nn,
            kind,
            mode: "A",
            cols: JKINDS[kind].slice(),
            rows: [],
            file: "",
            pages: 0,
            remarks: [],
          };
          (s || p).journals.push(j);
          logH("Создан журнал «" + j.name + "»");
          save();
          closeModal();
          go("#/j/" + j.id);
        },
      },
    ],
  );
};
A.newMat = (d) => {
  if (!guard("obj:" + d.p)) return;
  const p = proj(d.p);
  const m = {
    id: "m" + uid(),
    baseId: "",
    name: "Новый материал",
    category: "",
    brand: "",
    maker: "",
    note: "",
    docs: [],
  };
  p.materials.push(m);
  logH("Добавлен материал в «" + p.name + "»");
  save();
  go("#/m/" + m.id);
};
A.matFromBase = (d) => {
  if (!guard("obj:" + d.p)) return;
  const p = proj(d.p);
  const have = new Set(p.materials.map((m) => m.baseId).filter(Boolean));
  modal(
    "Добавить из базы паспортов",
    `<input id="fb-q" placeholder="Поиск по наименованию или № документа" oninput="document.querySelectorAll('#fb-l label').forEach(l=>l.style.display=l.dataset.s.includes(this.value.toLowerCase())?'':'none')"><div class="lst mt" id="fb-l">${S.lib.base.map((b) => `<label data-s="${esc((b.name + " " + b.docs.map((x) => x.num).join(" ")).toLowerCase())}"><input type="checkbox" value="${b.id}" ${have.has(b.id) ? "checked disabled" : ""}><span class="grow">${esc(b.name)}<div class="t2 small">${esc(b.docs.map((x) => x.type).join(", ") || "нет документов")}</div></span>${have.has(b.id) ? '<span class="pill p-n">уже в объекте</span>' : ""}</label>`).join("")}</div><div class="small mut mt">Материал будет связан с базой: обновления паспорта применяются автоматически.</div>`,
    [
      { l: "Отмена" },
      {
        l: "Добавить",
        c: "pri",
        f: () => {
          const ids = [
            ...document.querySelectorAll("#fb-l input:checked:not(:disabled)"),
          ].map((x) => x.value);
          if (!ids.length) {
            toast("Ничего не выбрано");
            return false;
          }
          ids.forEach((b) =>
            p.materials.push({
              id: "m" + uid(),
              baseId: b,
              name: "",
              category: "",
              brand: "",
              maker: "",
              note: "",
              docs: [],
            }),
          );
          logH(`Добавлено из базы паспортов: ${ids.length} (${p.name})`);
          save();
          closeModal();
          render();
          toast("Добавлено материалов: " + ids.length);
        },
      },
    ],
    "wide",
  );
};
A.baseToProj = (d) => {
  if (!guard(null)) return;
  const b = S.lib.base.find((x) => x.id === d.id);
  modal(
    "Добавить в объект",
    `<div class="lst">${S.projects
      .map((p) => {
        const has = p.materials.some((m) => m.baseId === b.id);
        return `<label><input type="checkbox" value="${p.id}" ${has ? "checked disabled" : ""}><span class="grow">${esc(p.name)}</span>${has ? '<span class="pill p-n">уже есть</span>' : ""}</label>`;
      })
      .join("")}</div>`,
    [
      { l: "Отмена" },
      {
        l: "Добавить",
        c: "pri",
        f: () => {
          const ids = [
            ...document.querySelectorAll(".dlg input:checked:not(:disabled)"),
          ].map((x) => x.value);
          ids.forEach((pid) =>
            proj(pid).materials.push({
              id: "m" + uid(),
              baseId: b.id,
              name: "",
              category: "",
              brand: "",
              maker: "",
              note: "",
              docs: [],
            }),
          );
          logH(`«${b.name}» добавлен в объекты: ${ids.length}`);
          save();
          closeModal();
          render();
        },
      },
    ],
  );
};
A.matUnlink = (d) => {
  if (!guard(entKey("mat", d.id))) return;
  const m = getEnt("mat", d.id);
  const b = baseOf(m);
  confirmBox(
    "Отвязать от базы",
    b
      ? "Будет создана независимая копия паспорта в объекте. Изменения в базе больше не будут применяться к этому материалу."
      : "Материал станет своим материалом объекта без документов.",
    () => {
      if (b) {
        Object.assign(m, {
          name: b.name,
          category: b.category,
          brand: b.brand,
          maker: b.maker,
          docs: clone(b.docs).map((x) => ({ ...x, id: uid() })),
        });
      } else m.name = m.name || "Материал";
      m.baseId = "";
      commit("Материал отвязан от базы паспортов", m);
    },
    "Отвязать",
  );
};
A.matToBase = (d) => {
  if (!guard(entKey("mat", d.id))) return;
  const m = getEnt("mat", d.id);
  if (!m.name.trim()) {
    toast("Укажите наименование");
    return;
  }
  const b = {
    id: "b" + uid(),
    name: m.name,
    category: m.category,
    brand: m.brand,
    maker: m.maker,
    docs: clone(m.docs),
  };
  S.lib.base.push(b);
  m.baseId = b.id;
  m.docs = [];
  commit(`«${b.name}» добавлен в базу паспортов`, m);
  toast("Добавлено в базу и связано с ней");
};
A.libNew = (d) => {
  if (!guard("lib")) return;
  const k = d.k;
  let o, h;
  if (k === "org") {
    o = {
      id: "o" + uid(),
      full: "",
      short: "Новая организация",
      role: "Подрядчик",
      inn: "",
      ogrn: "",
      address: "",
      sro: "",
      props: "",
      logo: "",
    };
    S.lib.orgs.push(o);
    h = "#/lib/orgs/" + o.id;
  }
  if (k === "per") {
    o = {
      id: "p" + uid(),
      fio: "",
      fioShort: "Новый представитель",
      position: "",
      orgId: S.lib.orgs[0]?.id || "",
      docRole: 1,
      authority: "",
      nrs: "",
      sign: "",
    };
    S.lib.people.push(o);
    Object.values(S.lib.signMatrix).forEach((l) => l.push(o.id));
    h = "#/lib/people/" + o.id;
  }
  if (k === "ord") {
    o = {
      id: "or" + uid(),
      name: "Новый документ",
      num: "",
      date: today(),
      orgId: S.lib.orgs[0]?.id || "",
      file: "",
      pages: 0,
    };
    S.lib.orders.push(o);
    h = "#/lib/orders";
  }
  if (k === "base") {
    o = {
      id: "b" + uid(),
      name: "Новый паспорт",
      category: "",
      brand: "",
      maker: "",
      docs: [],
    };
    S.lib.base.push(o);
    h = "#/lib/base/" + o.id;
  }
  if (k === "pf") {
    o = {
      id: "pf" + uid(),
      family: uid(),
      name: "Новый заказчик",

      date: today(),
      templates: [],
      quality: "once",
      naming: "{Тип}_{Номер}",
      reqFields: ["works", "place", "rd"],
      reqDocs: ["Титульный лист", "Реестр", "АОСР"],
      extra: "",
      logo: "",
    };
    S.lib.profiles.push(o);
    h = "#/lib/profiles/" + o.id;
  }
  logH("Создан(а) " + ENT_NAME[k]);
  save();
  go(h);
};

A.pfArr = (d, el) => {
  if (!guard("lib")) return;
  const x = prof(d.id);
  const arr = x[d.arr];
  const i = arr.indexOf(d.v);
  if (i < 0) arr.push(d.v);
  else arr.splice(i, 1);
  commit("Изменён профиль «" + x.name + "»", x);
};
A.signTog = (d) => {
  if (!guard("lib")) return;
  const l = S.lib.signMatrix[d.t];
  const i = l.indexOf(d.p);
  if (i < 0) l.push(d.p);
  else l.splice(i, 1);
  commit("Изменена матрица подписантов");
};
A.signPick = async (d) => {
  if (!guard("lib")) return;
  const [f] = await pickFiles("image/*");
  if (!f) return;
  const x = person(d.id);
  x.sign = await imgToData(f, 300);
  commit("Загружена подпись " + x.fioShort, x);
};
A.logoPick = async (d) => {
  if (!guard("obj:" + d.id)) return;
  const [f] = await pickFiles("image/*");
  if (!f) return;
  const p = proj(d.id);
  p.logo = await imgToData(f, 300);
  commit("Загружен логотип", p);
};
A.tplAdd = async () => {
  if (!guard("lib")) return;
  const [f] = await pickFiles(".docx");
  if (!f) return;
  const tags = await docxTags(f);
  const t = {
    id: "t" + uid(),
    name: f.name.replace(/\.docx$/i, ""),
    type: "Иной документ",
    file: f.name,
    tags,
    locked: false,
    date: today(),
  };
  S.lib.templates.push(t);
  const unk = tags.filter((x) => !knownTags().has(x));
  commit("Загружен шаблон «" + t.name + "»");
  toast(
    `Найдено тегов: ${tags.length}${unk.length ? ", неизвестных: " + unk.length : ""}`,
  );
};
A.tplReplace = async (d) => {
  if (!guard("lib")) return;
  const [f] = await pickFiles(".docx");
  if (!f) return;
  const t = tpl(d.id);
  t.file = f.name;
  t.tags = await docxTags(f);
  t.date = today();
  commit("Заменён шаблон «" + t.name + "»", t);
  toast("Тегов в файле: " + t.tags.length);
};

/* --- общие операции со строками и файлами --- */
A.rowAdd = (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const o = getEnt(d.ent, d.id);
  const arr = getPath(o, d.p);
  arr.push(ROWT[d.k](o));
  commit("", o);
};
A.rowRm = (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const o = getEnt(d.ent, d.id);
  const arr = getPath(o, d.p);
  const i = arr.findIndex((x) => x.id === d.r);
  if (i >= 0) arr.splice(i, 1);
  commit("Удалена строка: " + entLabel(d.ent, o), o);
};
A.remAdd = (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const o = getEnt(d.ent, d.id);
  o.remarks.push(ROWT.remark());
  commit("", o);
};
A.remRm = (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const o = getEnt(d.ent, d.id);
  o.remarks = o.remarks.filter((x) => x.id !== d.r);
  commit("", o);
};
A.extraAdd = (d) => {
  if (!guard("obj:" + d.p)) return;
  const p = proj(d.p);
  p.extra.push(ROWT.extra());
  commit("", p);
};
A.extraRm = (d) => {
  if (!guard("obj:" + d.p)) return;
  const p = proj(d.p);
  p.extra = p.extra.filter((x) => x.id !== d.x);
  commit("", p);
};
A.mv = (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const o = getEnt(d.ent, d.id);
  const arr = getPath(o, d.p);
  const i = +d.i,
    j = i + +d.d;
  if (j < 0 || j >= arr.length) return;
  [arr[i], arr[j]] = [arr[j], arr[i]];
  commit("", o);
};
A.pickPdf = async (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const [f] = await pickFiles(".pdf,application/pdf");
  if (!f) return;
  const o = getEnt(d.ent, d.id);
  const t = d.p ? getPath(o, d.p) : o;
  t.file = f.name;
  t.pages = await pdfPages(f);
  if ("stamped" in t) t.stamped = false;
  commit(`Загружен файл «${f.name}»`, o);
  toast(`${f.name}: ${t.pages} л. — файл скопирован в папку базы`);
};
A.schemeFile = async (d) => {
  if (!guard("sys:" + d.s)) return;
  const [f] = await pickFiles(".pdf,application/pdf");
  if (!f) return;
  const s = getEnt("sys", d.s);
  const sc = s.scheme;
  sc.file = f.name;
  sc.pages = await pdfPages(f);
  sc.stamped = false;
  sc.updated = nowStr();
  sc.updatedBy = APP.user;
  commit(`Загружена исполнительная схема ${s.code}`, s);
  toast(
    `Схема ${s.code}: ${sc.pages} л. Файл скопирован в папку базы, прежний файл заменён.`,
  );
};

A.stampApply = (d) => {
  if (!guard("sys:" + d.s)) return;
  const s = getEnt("sys", d.s);
  if (!s.scheme.file) {
    toast("Сначала загрузите файл схемы");
    return;
  }
  const p = ctx("sys", d.s).p;
  const { ov } = sheetSvg(s.scheme, { cipher: "", name: "", execId: "" });
  if (ov) {
    toast("Штамп перекрывает основную надпись — измените положение");
    return;
  }
  s.scheme.stamped = true;
  commit("Наложен штамп на схему " + s.code, s);
  toast(
    `Штамп наложен: ${s.subprofiles.length > 1 ? s.subprofiles.length + " варианта (по подпрофилям)" : "1 вариант"}`,
  );
};
A.ownPrev = (d) => {
  const c = ctx("act", d.id);
  const a = c.o;
  const x = a.schemes.find((q) => q.id === d.x);
  const sp = spOf(c.s, a.subs[0]);
  const { svg, ov } = sheetSvg(x, {
    cipher: c.s.cipher,
    name: x.name,
    execId: sp?.execId || c.s.scheme.execId,
    date: a.end,
  });
  modal(
    "Штамп: " + x.name,
    `<div class="g3 mb">${F("Положение штампа", "act", a.id, "schemes.#" + x.id + ".pos", x.pos, { opts: STAMP_POS })}${F("Ориентация", "act", a.id, "schemes.#" + x.id + ".orient", x.orient, { opts: ORIENT })}${F("Шифр РД", "act", a.id, "schemes.#" + x.id + ".rd", x.rd)}</div>${ov ? '<div class="alert al-r">Штамп перекрывает основную надпись</div>' : ""}<div class="sheetwrap">${svg}</div><div class="small mut mt">Исполнитель в штампе — из подпрофиля «${esc(sp?.name || "")}». Изменения применятся после закрытия окна.</div>`,
    [
      {
        l: "Закрыть",
        f: () => {
          render();
        },
      },
    ],
    "wide",
  );
};
/* --- акт --- */
A.subTog = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const a = getEnt("act", d.id);
  const i = a.subs.indexOf(d.sp);
  if (i < 0) a.subs.push(d.sp);
  else a.subs.splice(i, 1);
  commit("Изменены комплекты " + a.num, a);
};
A.actMatAdd = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const c = ctx("act", d.id);
  const a = c.o,
    p = c.p;
  if (!p.materials.length) {
    toast("В объекте нет материалов");
    return go("#/p/" + p.id + "/mats");
  }
  modal(
    "Материалы для " + a.num,
    `<div class="lst">${p.materials.map((m) => `<label><input type="checkbox" value="${m.id}" ${a.materials.includes(m.id) ? "checked" : ""}><span class="grow">${esc(mName(m))}</span>${m.baseId ? '<span class="pill p-b">База</span>' : ""}<span class="pill p-n">${mDocs(m).length} док.</span></label>`).join("")}</div>`,
    [
      { l: "Отмена" },
      {
        l: "Применить",
        c: "pri",
        f: () => {
          const ids = [
            ...document.querySelectorAll(".dlg .lst input:checked"),
          ].map((x) => x.value);
          a.materials = a.materials
            .filter((m) => !pMat(p, m) || ids.includes(m))
            .concat(ids.filter((m) => !a.materials.includes(m)));
          Object.keys(a.aikLinks).forEach((m) => {
            if (!a.materials.includes(m)) delete a.aikLinks[m];
          });
          a.materials.forEach((m) => {
            if (!a.aikLinks[m]) {
              const k = c.s.aik.find((x) => x.materialId === m);
              if (k) a.aikLinks[m] = k.id;
            }
          });
          closeModal();
          commit("Изменены материалы " + a.num, a);
        },
      },
    ],
    "wide",
  );
};
A.actMatRm = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const a = getEnt("act", d.id);
  a.materials = a.materials.filter((m) => m !== d.m);
  delete a.aikLinks[d.m];
  commit("Изменены материалы " + a.num, a);
};
A.photoAdd = async (d) => {
  if (!guard(entKey("act", d.id))) return;
  const fs = await pickFiles("image/*", true);
  if (!fs.length) return;
  const a = getEnt("act", d.id);
  for (const f of fs) {
    a.photos.push({ id: uid(), cap: "", img: await imgToData(f) });
  }
  A.photoAuto(d, null, true);
  toast(
    `Загружено фото: ${fs.length}. Сохранены в карточке акта внутри этого браузера`,
  );
};
A.photoAuto = (d, el, silent) => {
  const a = getEnt("act", d.id);
  a.photos.forEach((p, i) => {
    if (!p.cap || !silent)
      p.cap = `Фото ${i + 1}. ${a.works}. ${a.place}. ${fmtD(a.end)}`;
  });
  commit("Обновлены подписи фото " + a.num, a);
};
A.photoRepl = async (d) => {
  if (!guard(entKey("act", d.id))) return;
  const [f] = await pickFiles("image/*");
  if (!f) return;
  const a = getEnt("act", d.id);
  a.photos.find((x) => x.id === d.p).img = await imgToData(f);
  commit("", a);
};
A.photoPrev = (d) => {
  const a = getEnt("act", d.id);
  const n = +a.photoLayout || 2;
  const pages = [];
  for (let i = 0; i < a.photos.length; i += n)
    pages.push(a.photos.slice(i, i + n));
  modal(
    "Фототаблица к " + a.num,
    `<div class="pages">${pages.map((pg, k) => `<div class="pg"><div class="hh">Фототаблица к ${esc(a.type)} № ${esc(a.num)}</div><div class="cells" style="grid-template-columns:${n === 4 ? "1fr 1fr" : "1fr"};grid-template-rows:repeat(${n === 4 ? 2 : n},1fr)">${pg.map((p) => `<div class="cell"><div class="im"${p.img ? ` style="background-image:url(${p.img})"` : ""}></div><div class="cp">${esc(p.cap)}</div></div>`).join("")}</div><div class="ft">Лист ${k + 1} из ${pages.length}</div></div>`).join("")}</div>`,
    [{ l: "Закрыть" }],
    "xwide",
  );
};
/* --- выделение и массовые операции --- */
A.selOne = (d) => {
  S.ui.sel[d.id] = !S.ui.sel[d.id];
  if (!S.ui.sel[d.id]) delete S.ui.sel[d.id];
  save();
  render();
};
A.selAll = (d) => {
  const s = getEnt("sys", d.s);
  const all = s.acts.every((a) => S.ui.sel[a.id]);
  s.acts.forEach((a) => {
    if (all) delete S.ui.sel[a.id];
    else S.ui.sel[a.id] = true;
  });
  save();
  render();
};
A.selClear = () => {
  S.ui.sel = {};
  save();
  render();
};
const selActs = () =>
  Object.keys(S.ui.sel)
    .map((id) => ctx("act", id))
    .filter((c) => c.o);
A.massStatus = (d) => {
  if (!guard()) return;
  const L = selActs();
  L.forEach((c) => {
    c.o.status = d.v;
    touch(c.o);
  });
  S.ui.sel = {};
  commit(`Статус «${d.v}» для актов: ${L.length}`);
};
A.massDup = () => {
  if (!guard()) return;
  const L = selActs();
  L.forEach((c) => {
    const a = newActObj(c.s, c.o);
    a.type = c.o.type;
    a.num = nextNum(c.s, a.type);
    c.s.acts.push(a);
  });
  S.ui.sel = {};
  commit(`Дублировано актов: ${L.length}`);
  toast("Создано копий: " + L.length);
};
A.massDel = () => {
  if (!guard()) return;
  const L = selActs();
  confirmBox(
    "Удалить акты",
    `Переместить в корзину актов: ${L.length}?`,
    () => {
      L.forEach((c) => toTrash("act", c.o.id));
      S.ui.sel = {};
      save();
      render();
    },
  );
};
/* --- подпрофили --- */
A.spAdd = (d) => {
  if (!guard("sys:" + d.s)) return;
  const s = getEnt("sys", d.s);
  const ref = s.subprofiles[0];
  const sp = {
    id: "sp" + uid(),
    name: s.code + " — Заказчик " + (s.subprofiles.length + 1),
    profileId: ref?.profileId || S.lib.profiles[0]?.id,
    execId: ref?.execId || "",
    signers: { ...(ref?.signers || {}) },
  };
  s.subprofiles.push(sp);
  s.acts.forEach((a) => a.subs.push(sp.id));
  commit("Добавлен подпрофиль " + sp.name, s);
  toast(
    "Все акты системы включены в новый комплект — лишние можно снять в карточках актов",
  );
};
A.spRm = (d) => {
  if (!guard("sys:" + d.s)) return;
  const s = getEnt("sys", d.s);
  const sp = spOf(s, d.sp);
  confirmBox(
    "Удалить подпрофиль",
    `Удалить «${esc(sp.name)}»? Акты останутся в системе, но исчезнут из этого комплекта.`,
    () => {
      s.subprofiles = s.subprofiles.filter((x) => x.id !== d.sp);
      s.acts.forEach((a) => {
        a.subs = a.subs.filter((x) => x !== d.sp);
      });
      commit("Удалён подпрофиль " + sp.name, s);
    },
  );
};
/* --- журналы --- */
A.jMode = (d) => {
  if (!guard(entKey("jr", d.id))) return;
  const j = getEnt("jr", d.id);
  j.mode = d.v;
  commit("", j);
};
A.jRowAdd = (d) => {
  if (!guard(entKey("jr", d.id))) return;
  const j = getEnt("jr", d.id);
  j.rows.push({
    id: uid(),
    c: j.cols.map((x, i) => (i === 0 ? fmtD(today()) : "")),
  });
  commit("", j);
};
A.jColAdd = (d) => {
  if (!guard(entKey("jr", d.id))) return;
  const j = getEnt("jr", d.id);
  j.cols.push("Новая колонка");
  commit("", j);
};
A.jColRm = (d) => {
  if (!guard(entKey("jr", d.id))) return;
  const j = getEnt("jr", d.id);
  const i = +d.i;
  j.cols.splice(i, 1);
  j.rows.forEach((r) => r.c.splice(i, 1));
  commit("", j);
};
A.jFromActs = (d) => {
  if (!guard(entKey("jr", d.id))) return;
  const c = ctx("jr", d.id);
  const j = c.o;
  const have = new Set(j.rows.map((r) => r.c[3]));
  const L = (c.s ? [c.s] : c.p.systems)
    .flatMap((s) => sortActs(s.acts).map((a) => ({ a, s })))
    .filter((x) => !have.has(x.a.num));
  L.forEach(({ a, s }) =>
    j.rows.push({
      id: uid(),
      c: [
        fmtD(a.end),
        a.works + ". " + a.place + " (" + s.code + ")",
        (person(signer(a, s.subprofiles[0], 1))?.fioShort || "") +
          ", " +
          (person(signer(a, s.subprofiles[0], 1))?.position || ""),
        a.num,
      ],
    }),
  );
  commit("Заполнен журнал из актов", j);
  toast("Добавлено записей: " + L.length);
};
/* --- удаление и корзина --- */
A.del = (d) => {
  if (d.ent === "proj" || d.ent === "sys") {
    const lk = childLockedBy((d.ent === "proj" ? "obj:" : "sys:") + d.id);
    if (lk) {
      toast(`Нельзя удалить: ${lockName(lk.k)} редактирует ${lk.l.user}`);
      return;
    }
  }
  if (!guard(d.ent === "proj" ? null : entKey(d.ent, d.id))) return;
  const ent = d.ent,
    id = d.id;
  const o = getEnt(ent, id);
  if (!o) return;
  const c = ctx(ent, id);
  let txt = `Переместить ${esc(entLabel(ent, o))} в корзину?`;
  if (ent === "sys")
    txt += ` Вместе с системой — ${o.acts.length} актов, ${o.aik.length} АИК и журналы.`;
  if (ent === "proj") txt += " Вместе со всеми системами и актами.";
  if (ent === "mat") {
    const n = c.p.systems.reduce(
      (k, s) => k + s.acts.filter((a) => a.materials.includes(id)).length,
      0,
    );
    if (n) txt += ` Материал указан в ${n} актах — проверка покажет ошибки.`;
  }
  if (ent === "base") {
    const u = baseUse(o);
    if (u.length)
      txt += ` Паспорт используется в объектах (${u.length}) — там он станет независимой копией.`;
  }
  confirmBox("Удаление", txt, () => {
    if (ent === "base")
      S.projects.forEach((p) =>
        p.materials.forEach((m) => {
          if (m.baseId === id) {
            Object.assign(m, {
              name: o.name,
              category: o.category,
              brand: o.brand,
              maker: o.maker,
              docs: clone(o.docs),
            });
            m.baseId = "";
          }
        }),
      );
    toTrash(ent, id);
    save();
    const back = {
      proj: "#/home",
      sys: "#/p/" + c.p?.id,
      act: "#/s/" + c.s?.id,
      aik: "#/s/" + c.s?.id + "/aik",
      jr: c.s ? "#/s/" + c.s.id + "/jr" : "#/p/" + c.p?.id + "/ozhr",
      mat: "#/p/" + c.p?.id + "/mats",
      base: "#/lib/base",
      org: "#/lib/orgs",
      per: "#/lib/people",
      ord: "#/lib/orders",
      pf: "#/lib/profiles",
      tpl: "#/lib/templates",
    }[ent];
    toast("Перемещено в корзину");
    go(back);
  });
};
A.trRestore = (d) => {
  if (!guard(null)) return;
  const i = S.trash.findIndex((t) => t.id === d.id);
  const t = S.trash[i];
  const c = { p: proj(t.ctx?.pid), s: getEnt("sys", t.ctx?.sid) };
  const arr = container(t.ent, c);
  if (!arr) {
    toast("Родительский элемент удалён — сначала восстановите его");
    return;
  }
  arr.push(t.item);
  S.trash.splice(i, 1);
  commit("Восстановлен(а) " + entLabel(t.ent, t.item));
  toast("Восстановлено");
};
A.trPurge = (d) => {
  if (!guard(null)) return;
  confirmBox(
    "Удалить навсегда",
    "Элемент будет удалён без возможности восстановления.",
    () => {
      S.trash = S.trash.filter((t) => t.id !== d.id);
      commit("Удалено из корзины");
    },
  );
};
A.trEmpty = () => {
  if (!guard(null)) return;
  confirmBox(
    "Очистить корзину",
    `Удалить навсегда ${S.trash.length} элементов?`,
    () => {
      S.trash = [];
      commit("Корзина очищена");
    },
    "Очистить",
  );
};
/* --- сборка --- */
function curVol() {
  const p = proj(S.ui.build.pid) || S.projects[0];
  const vols = volumeList(p);
  return { p, vol: vols.find((v) => v.key === S.ui.build.vol) || vols[0] };
}
function volCfg() {
  const { p, vol } = curVol();
  const k = p.id + "|" + vol.key;
  return (S.volCfg[k] = S.volCfg[k] || {});
}
A.blkTog = (d) => {
  if (!guard(null)) return;
  const c = volCfg();
  c.off = c.off || [];
  const i = c.off.indexOf(d.k);
  if (i < 0) c.off.push(d.k);
  else c.off.splice(i, 1);
  save();
  render();
};
A.blkMv = (d) => {
  if (!guard(null)) return;
  const { p, vol } = curVol();
  const keys = blocksFor(p, vol).map((b) => b.key);
  const i = keys.indexOf(d.k),
    j = i + +d.d;
  if (j < 0 || j >= keys.length) return;
  [keys[i], keys[j]] = [keys[j], keys[i]];
  volCfg().order = keys;
  save();
  render();
};
A.docMv = (d) => {
  if (!guard(null)) return;
  const { p, vol } = curVol();
  const b = blocksFor(p, vol).find((x) => x.key === d.k);
  const ids = b.items.map((x) => x.id);
  const i = ids.indexOf(d.i),
    j = i + +d.d;
  if (j < 0 || j >= ids.length) return;
  [ids[i], ids[j]] = [ids[j], ids[i]];
  const c = volCfg();
  c.docs = c.docs || {};
  c.docs[d.k] = ids;
  save();
  render();
};
A.volReset = () => {
  const { p, vol } = curVol();
  delete S.volCfg[p.id + "|" + vol.key];
  save();
  render();
};
A.regCsv = () => {
  const { p, vol } = curVol();
  const { rows } = registry(p, vol);
  download(
    slug(p.name + "_" + vol.short) + "_реестр.csv",
    csv([
      ["№", "Тип", "Наименование", "Номер и дата", "Листы", "Файл"],
      ...rows
        .filter((r) => !r.book)
        .map((r) => [
          r.n,
          r.type,
          r.name,
          r.nd,
          r.from === r.to ? r.from : r.from + "–" + r.to,
          r.file,
        ]),
    ]),
    "text/csv;charset=utf-8",
  );
  toast("Реестр выгружен в CSV");
};
A.titlePrev = () => {
  const { p, vol } = curVol();
  const pf = vol.sp ? prof(vol.sp.profileId) : null;
  modal(
    "Титульный лист",
    `<div class="paper" style="width:auto;text-align:center;padding:48px">${p.logo ? `<img src="${p.logo}" style="height:46px;margin-bottom:12px">` : ""}<div>${esc(p.developer || "")}</div><div style="margin-top:70px;font-size:17px"><b>ИСПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ</b></div><div style="margin-top:16px">${esc(p.name)}</div><div>${esc(p.address)}</div><div style="margin-top:22px"><b>${esc(vol.title)}</b></div><div style="margin-top:12px">Шифр: ${esc(vol.s?.cipher || p.cipher)}</div><div style="margin-top:80px">${esc(p.genContractor)}</div><div>${new Date().getFullYear()}</div><div class="pc" style="margin-top:20px">Шаблон: ${esc(pf ? (pf.templates.map(tpl).find((t) => t && t.type === "Титульный лист") || {}).name || "не найден" : "по умолчанию")}</div></div>`,
    [{ l: "Закрыть" }],
    "wide",
  );
};

/* --- резервные копии, данные --- */

A.exportJson = () => {
  download(
    "stroiid_" + today() + ".json",
    JSON.stringify(S, null, 1),
    "application/json",
  );
  toast("Данные выгружены");
};
A.importJson = async () => {
  const [f] = await pickFiles(".json");
  if (!f) return;
  try {
    const d = JSON.parse(await f.text());
    if (!d.meta || d.meta.v !== 30 || !d.projects) throw new Error("формат");
    d.locks = S.locks;
    d.ui = S.ui;
    S = d;
    IX = null;
    logH("Импорт из " + f.name);
    save();
    go("#/home");
    toast("Данные загружены");
  } catch (e) {
    toast("Файл не подходит: нужен экспорт СтройИД v3");
  }
};
A.resetDemo = () =>
  confirmBox(
    "Восстановить демо-данные",
    "Текущие данные будут заменены демонстрационными. ",
    () => {
      S = seed();
      IX = null;
      save();
      go("#/home");
      render();
    },
    "Восстановить",
  );
A.scanRm = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const a = getEnt("act", d.id);
  a.scan = { file: "", pages: 0 };
  commit("Убран скан " + a.num, a);
};

/* =====================================================================
   v3: база = папка на Яндекс Диске, метки редактирования, файлы, импорт
   ===================================================================== */
const LOGO = `<svg width="40" height="40" viewBox="0 0 32 32" fill="none" aria-label="СтройИД"><rect width="32" height="32" rx="8" fill="#2456c9"/><path d="M9 23V13.5L16 9l7 4.5V23" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/><path d="M13 23v-5h6v5" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/><circle cx="23.5" cy="8.5" r="2.5" fill="#ffc94a"/></svg>`;
const PULSE_MIN = 2,
  STALE_MIN = 30;

/* ---------- метки редактирования (.locks/ИМЯ_КОМПЬЮТЕР.json) ---------- */
const isMe = (l) => l.user === APP.user && l.pc === APP.pc;
const isFresh = (l) => Date.now() - Date.parse(l.pulse) < STALE_MIN * 60e3;
const agoS = (s) => {
  const m = Math.max(0, Math.round((Date.now() - Date.parse(s)) / 60e3));
  return m < 60 ? m + " мин" : Math.floor(m / 60) + " ч " + (m % 60) + " мин";
};
function lockInfo(key) {
  const L = S.locks[key] || [];
  const fr = L.filter(isFresh).sort((a, b) => a.since.localeCompare(b.since));
  const owner = fr[0] || null;
  return {
    mine: L.find(isMe) || null,
    owner,
    blockedBy: owner && !isMe(owner) ? owner : null,
    stale: L.filter((l) => !isMe(l) && !isFresh(l)),
  };
}
function lockName(key) {
  if (!key) return "";
  const [t, id] = key.split(":");
  if (t === "sys") return "систему " + (getEnt("sys", id)?.code || "");
  if (t === "obj")
    return "общие данные объекта «" + (proj(id)?.name || "") + "»";
  return "справочники";
}
function routeKey() {
  if (!S) return null;
  const r = route();
  const k = r[0],
    id = r[1];
  const X = ix();
  if (k === "s") return X.sys[id] ? "sys:" + id : null;
  if (k === "a") return X.act[id] ? "sys:" + X.act[id].s.id : null;
  if (k === "k") return X.aik[id] ? "sys:" + X.aik[id].s.id : null;
  if (k === "j") {
    const e = X.jr[id];
    return e ? (e.s ? "sys:" + e.s.id : "obj:" + e.p.id) : null;
  }
  if (k === "p") return X.proj[id] ? "obj:" + id : null;
  if (k === "m") return X.mat[id] ? "obj:" + X.mat[id].p.id : null;
  if (k === "lib") return "lib";
  return null;
}
function entKey(ent, id) {
  if (["ui", "root", "app"].includes(ent)) return null;
  if (LIBK[ent]) return "lib";
  if (ent === "proj") return "obj:" + id;
  if (ent === "sys") return "sys:" + id;
  const c = ctx(ent, id);
  if (ent === "mat") return c.p ? "obj:" + c.p.id : null;
  if (c.s) return "sys:" + c.s.id;
  if (c.p) return "obj:" + c.p.id;
  return null;
}
function takeLock(key) {
  const L = (S.locks[key] = S.locks[key] || []);
  let m = L.find(isMe);
  const isNew = !m;
  if (!m) {
    m = { user: APP.user, pc: APP.pc, since: iso(), pulse: iso() };
    L.push(m);
  } else m.pulse = iso();
  if (isNew && key === routeKey() && !$("#content .lockbar")) {
    $("#content").insertAdjacentHTML("afterbegin", lockBar(key));
    renderTree();
    renderStatus();
  }
}
function releaseMine(keep) {
  if (!S || !S.locks) return false;
  let ch = false;
  Object.keys(S.locks).forEach((k) => {
    if (k === keep) return;
    const n = S.locks[k].length;
    S.locks[k] = S.locks[k].filter((l) => !isMe(l));
    if (S.locks[k].length !== n) ch = true;
    if (!S.locks[k].length) delete S.locks[k];
  });
  return ch;
}
function childLockedBy(key) {
  const [t, id] = key.split(":");
  const keys = [key];
  if (t === "obj") {
    const p = proj(id);
    p?.systems.forEach((s) => keys.push("sys:" + s.id));
  }
  for (const k of keys) {
    const L = S.locks[k] ? lockInfo(k) : null;
    if (L && L.blockedBy) return { k, l: L.blockedBy };
  }
  return null;
}
function lockBar(key) {
  if (!key || !S.locks[key]) return "";
  const L = lockInfo(key);
  const n = esc(lockName(key));
  if (L.blockedBy)
    return `<div class="lockbar o">${ic("lock")}<span class="grow">Только просмотр: ${n} сейчас редактирует <b>${esc(L.blockedBy.user)}</b> (${esc(L.blockedBy.pc)}) с ${hm(L.blockedBy.since)}. Изменения появятся у вас автоматически.</span></div>`;
  if (L.stale.length && !L.mine) {
    const x = L.stale[0];
    return `<div class="lockbar s">${ic("lock")}<span class="grow">Брошенная метка: <b>${esc(x.user)}</b> (${esc(x.pc)}) — нет пульса ${esc(agoS(x.pulse))}. Снимите метку, чтобы редактировать ${n}.</span>${B("Снять метку", "lockStale", `data-k="${key}"`, "sm")}</div>`;
  }
  if (L.mine)
    return `<div class="lockbar m">${ic("lock")}<span class="grow">Вы редактируете ${n} с ${hm(L.mine.since)} — у коллег открыто только для просмотра.</span>${B("Завершить редактирование", "lockRelease", `data-k="${key}"`, "sm")}</div>`;
  return "";
}
function lockMark(key) {
  if (!S.locks[key]) return "";
  const L = lockInfo(key);
  if (L.blockedBy)
    return `<span class="lk o" title="Редактирует ${esc(L.blockedBy.user)} (${esc(L.blockedBy.pc)}) с ${hm(L.blockedBy.since)}">${ic("lock", "")}</span>`;
  if (L.mine)
    return `<span class="lk m" title="Вы редактируете">${ic("lock", "")}</span>`;
  if (L.stale.length)
    return `<span class="lk s" title="Брошенная метка: ${esc(L.stale[0].user)}, нет пульса ${esc(agoS(L.stale[0].pulse))}">${ic("lock", "")}</span>`;
  return "";
}
function lastForeign() {
  const h = S.history.find((x) => x.user !== APP.user);
  return h ? h.ts.split(", ").pop() + ", " + h.user : "";
}
function renderStatus() {
  if (!S) return;
  const k = routeKey();
  const L = k && S.locks[k] ? lockInfo(k) : null;
  const lf = lastForeign();
  $("#status").innerHTML =
    `<span class="si cl shr" data-a="showInFolder" data-path="${esc(APP.current)}" title="${esc(APP.current)} — показать в проводнике">${ic("folder")}<span>${esc(APP.current)}</span></span><span class="si">${ic("user")}${esc(APP.user)} · ${esc(APP.pc)}</span>
 ${k ? `<span class="si">${ic("lock")}${L && L.blockedBy ? "Только просмотр — " + esc(L.blockedBy.user) : L && L.mine ? "Вы редактируете · пульс " + hm(L.mine.pulse) : "Свободно"}</span>` : ""}<span class="grow"></span>
 ${lf ? `<span class="si shr shr2" title="Программа следит за папкой базы и сразу подхватывает изменения коллег">${ic("sync")}<span>Изменения коллег подхватываются автоматически · ${esc(lf)}</span></span>` : ""}<span class="si">Сохранено ${esc((S.ui.saved || "").split(", ")[1] || "")}</span>`;
}
// Desktop uses a process lock, no browser heartbeat.
window.addEventListener("beforeunload", () => {
  if (S && releaseMine(null)) {
    try {
      localStorage.setItem(LSP + APP.current, JSON.stringify(S));
    } catch (e) {}
  }
});
A.lockRelease = (d) => {
  if (S.locks[d.k]) {
    S.locks[d.k] = S.locks[d.k].filter((l) => !isMe(l));
    if (!S.locks[d.k].length) delete S.locks[d.k];
  }
  save();
  render();
  toast("Редактирование завершено, метка снята");
};
A.lockStale = (d) => {
  const L = lockInfo(d.k);
  const x = L.stale[0];
  if (!x) return;
  confirmBox(
    "Брошенная метка",
    `<p style="margin-top:0"><b>${esc(x.user)}</b> (${esc(x.pc)}) взял(а) ${esc(lockName(d.k))} ${fmtD(x.since.slice(0, 10))} в ${hm(x.since)}, но метка не обновлялась ${esc(agoS(x.pulse))}. Скорее всего, программа у коллеги закрылась аварийно или компьютер выключен.</p><p class="small mut" style="margin-bottom:0">Если коллега всё-таки работает без интернета, его изменения не потеряются: при сохранении появится окно сравнения версий.</p>`,
    () => {
      S.locks[d.k] = S.locks[d.k].filter((l) => isMe(l) || isFresh(l));
      if (!S.locks[d.k].length) delete S.locks[d.k];
      logH(`Снята брошенная метка ${x.user} (${lockName(d.k)})`);
      save();
      render();
      toast("Метка снята — можно редактировать");
    },
    "Снять метку",
  );
};

/* ---------- имитация совместной работы ---------- */
const COLLEAGUE = { user: "Кузнецова А. В.", pc: "PTO-02" };
