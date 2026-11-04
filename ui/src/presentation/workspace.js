/* Full СтройИД workspace: retain the original data model and editors. */
const originalViews = {
  home: V.home,
  p: V.p,
  s: V.s,
  a: V.a,
  settings: V.settings,
  build: V.build,
};
const legacyBody = (html) => {
  const pos = html.indexOf('class="tabs"');
  if (pos < 0) return html;
  const end = html.indexOf("</div>", pos);
  return html.slice(end + 6, -6);
};
const tile = (href, title, text, count, ico = "doc") =>
  `<a class="worktile" href="${href}"><span class="tileic">${ic(ico)}</span><span class="grow"><b>${esc(title)}</b><p>${esc(text)}</p><span class="tilefoot">${esc(count)}</span></span></a>`;
const countActs = (p) => p.systems.reduce((n, s) => n + s.acts.length, 0);
const countDone = (p) =>
  p.systems.reduce(
    (n, s) => n + s.acts.filter((a) => a.status === "Готово").length,
    0,
  );
const activeSystem = () => {
  const r = route();
  if (r[0] === "s") return ctx("sys", r[1]).s || ctx("sys", r[1]).o;
  if (["a", "k", "j"].includes(r[0]))
    return ctx({ a: "act", k: "aik", j: "jr" }[r[0]], r[1]).s;
  return null;
};
const resourceList = (s) => [
  {
    id: "system",
    name: "Комплект исполнительных схем " + s.code,
    record: s.scheme,
    kind: "system",
    owner: null,
  },
  ...(s.sketches || []).map((x) => ({
    id: x.id,
    name: x.name,
    record: x,
    kind: "extra",
    owner: null,
  })),
  ...s.acts.flatMap((a) =>
    a.schemes.map((x) => ({
      id: x.id,
      name: x.name,
      record: x,
      kind: "act",
      owner: a,
    })),
  ),
];
function linkedSchemes(a, s) {
  return (a.schemeLinks || []).map((link) => ({
    link,
    item: resourceList(s).find((x) => x.id === link.id),
  }));
}
function ensureWorkspace() {
  if (!S) return;
  S.projects.forEach((p) => {
    if (!p.name?.trim()) p.name = p.short || "";
    delete p.short;
    p.admin = p.admin || [];
    p.systems.forEach((s) => {
      s.sketches = s.sketches || [];
      s.trials = s.trials || [];
      s.acts.forEach((a) => {
        a.schemeLinks = a.schemeLinks || [];
        a.testLinks = a.testLinks || [];
      });
    });
  });
}
function systemNav(s, tab) {
  return tabs("#/s/" + s.id, tab, [
    ["overview", "Обзор"],
    ["acts", "Акты", s.acts.length],
    ["schemes", "Схемы", resourceList(s).length],
    ["materials", "Материалы", usedMaterials(s).size],
    ["aik", "Входной контроль", s.aik.length],
    [
      "trials",
      "Испытания",
      s.trials.length + s.acts.reduce((n, a) => n + a.tests.length, 0),
    ],
    ["jr", "Журналы", s.journals.length],
    ["subs", "Комплекты и подписанты"],
    ["params", "Настройки"],
  ]);
}
function usedMaterials(s) {
  return new Set(
    s.acts
      .flatMap((a) => a.materials)
      .concat(
        s.aik.map((k) => k.materialId),
        s.materialIds || [],
      ),
  );
}
function renderTree() {
  if (!S) return;
  const r = route(),
    p = curProject(),
    s = activeSystem();
  const nav = (h, label, ico, on, count) =>
    `<div class="tn${on ? " on" : ""}"><a href="${h}">${ic(ico)}<span class="lb">${esc(label)}</span>${count !== undefined ? `<span class="ct">${count}</span>` : ""}</a></div>`;
  let h = nav(
    "#/home",
    "Все объекты",
    "home",
    r[0] === "home",
    S.projects.length,
  );
  h +=
    '<div class="sh">Объекты ' +
    B(
      "+",
      "newProject",
      'title="Создать объект" aria-label="Создать объект"',
      "sm icon ghost",
    ) +
    "</div>";
  S.projects.forEach((x) => {
    h += nav("#/p/" + x.id, x.name, "bld", p?.id === x.id && !s);
    if (p?.id === x.id) {
      h += '<div class="navbranch">';
      sortedSys(x).forEach(
        (y) =>
          (h += nav(
            "#/s/" + y.id,
            y.code + " · " + y.name,
            "sys",
            s?.id === y.id,
          )),
      );
      h += nav(
        "#/p/" + x.id + "/general",
        "Общие разделы объекта",
        "folder",
        r[0] === "p" && r[2] === "general",
      );
      h += nav("#/build/" + x.id, "Сборка томов", "layers", r[0] === "build");
      h += "</div>";
    }
  });
  if (s) {
    h += `<div class="sh">Система ${esc(s.code)}</div>`;
    const sec =
      r[0] === "s"
        ? r[2] || "overview"
        : r[0] === "a"
          ? "acts"
          : r[0] === "k"
            ? "aik"
            : r[0] === "j"
              ? "jr"
              : "";
    for (const [t, n, ico, count] of [
      ["overview", "Обзор системы", "sys"],
      ["acts", "Акты", "doc", s.acts.length],
      ["schemes", "Исполнительные схемы", "stamp", resourceList(s).length],
      ["materials", "Материалы и паспорта", "box", usedMaterials(s).size],
      ["aik", "Входной контроль", "check", s.aik.length],
      [
        "trials",
        "Испытания и протоколы",
        "doc",
        s.trials.length + s.acts.reduce((n, a) => n + a.tests.length, 0),
      ],
      ["jr", "Специальные журналы", "stamp", s.journals.length],
    ])
      h += nav("#/s/" + s.id + "/" + t, n, ico, sec === t, count);
  }
  h +=
    '<div class="sh">Общие справочники</div>' +
    nav(
      "#/lib/base",
      "Материалы и паспорта",
      "box",
      r[0] === "lib" && r[1] === "base",
    ) +
    nav(
      "#/lib/orgs",
      "Организации и подписанты",
      "users",
      r[0] === "lib" && ["orgs", "people", "orders", "sign"].includes(r[1]),
    ) +
    nav(
      "#/lib/profiles",
      "Профили и шаблоны",
      "tag",
      r[0] === "lib" && ["profiles", "templates", "tags"].includes(r[1]),
    );
  h +=
    '<div class="sh">Сервис</div>' +
    nav("#/import", "Импорт в разделы", "imp", r[0] === "import") +
    nav("#/settings", "Сохранение и настройки", "gear", r[0] === "settings");
  $("#tree").innerHTML = h;
  $("#sidefoot").innerHTML =
    `<div class="ava">ПТО</div><div class="grow"><b>${esc(APP.user)}</b><br><small class="mut">Локальное приложение</small></div>`;
}
function renderTop() {
  const p = curProject();
  $("#top").innerHTML =
    `${B("☰", "mobileNav", 'aria-label="Открыть навигацию"', "mobile-menu icon")}<div class="search">${ic("search", "")}<input id="gsearch" type="text" placeholder="Найти объект, акт, материал…" value="${esc(S.ui.q || "")}"></div><div class="sp"></div><span class="status-tag top-desktop">Desktop 0.5</span>${p ? B(ic("layers") + " Сборка томов", "nav", `data-h="#/build/${p.id}"`, "pri top-build") : ""}${B(ic("download"), "exportJson", 'title="Сохранить проект JSON" aria-label="Сохранить проект"', "icon")}${B(ic("more"), "menu", 'aria-label="Меню проекта" title="Меню проекта"', "icon")}`;
}
function renderStatus() {
  if (!S) return;
  $("#status").innerHTML =
    `<span class="si">${ic("check")}Карточки сохраняются в этом браузере</span><span class="si shr">Последнее изменение: ${esc(S.ui.saved || "—")}</span><span class="grow"></span><span class="si">${S.projects.length} объекта</span>`;
}
A.mobileNav = () => document.body.classList.toggle("nav-open");
const originalNav = A.nav;
A.nav = (d) => {
  document.body.classList.remove("nav-open");
  originalNav(d);
};
window.addEventListener("hashchange", () =>
  document.body.classList.remove("nav-open"),
);
A.menu = () => {
  modal(
    "Проект и сохранение",
    `<div class="section-grid">${tile("#/settings", "Настройки", "Имя пользователя, режим просмотра и работа с данными", "Открыть", "gear")}${tile("#/settings/trash", "Корзина", "Восстановление удалённых объектов и записей", S.trash.length + " записей", "trash")}</div><div class="row mt">${B("Сохранить проект JSON", "exportJson")}${B("Открыть проект JSON", "importJson")}</div>`,
    [{ l: "Закрыть" }],
    "wide",
  );
};
V.home = () => {
  const total = S.projects.reduce((n, p) => n + countActs(p), 0),
    done = S.projects.reduce((n, p) => n + countDone(p), 0);
  return `<div class="page">${hdr("Объекты", "Выберите объект — далее работайте внутри нужной инженерной системы.", B(ic("plus") + " Новый объект", "newProject", "", "pri"))}<div class="kpis"><div class="kpi"><div class="v">${S.projects.length}</div><div class="l">объекта в работе</div></div><div class="kpi"><div class="v">${S.projects.reduce((n, p) => n + p.systems.length, 0)}</div><div class="l">инженерных систем</div></div><div class="kpi"><div class="v">${total}</div><div class="l">актов в базе</div></div><div class="kpi"><div class="v">${done}</div><div class="l">актов отмечено готовыми</div></div></div><div class="objg">${S.projects
    .map((p) => {
      const n = countActs(p),
        d = countDone(p),
        C = check(p);
      return `<a class="sc" href="#/p/${p.id}"><div class="row"><span class="code">${esc(p.name)}</span><span class="grow"></span>${ic("bld")}</div><div class="nm">${esc(p.address || "Адрес не заполнен")}</div><div class="row">${p.systems.map((s) => `<span class="pill p-n">${esc(s.code)}</span>`).join("")}</div><div class="numline"><span><b>${p.systems.length}</b> систем</span><span><b>${n}</b> актов</span><span><b>${C.E.length + C.W.length}</b> замечаний</span></div><div class="prog"><i style="width:${n ? Math.round((d / n) * 100) : 0}%"></i></div><div class="small mut">Готовность актов: ${d} из ${n}</div></a>`;
    })
    .join(
      "",
    )}</div><div class="homelead"><h2>Общие справочники</h2><span class="sectionhint">Используются на нескольких объектах</span></div><div class="section-grid">${tile("#/lib/base", "Материалы и паспорта", "Каталог материалов, паспортов и сертификатов", S.lib.base.length + " материалов", "box")}${tile("#/lib/orgs", "Организации и подписанты", "Участники строительства, представители и полномочия", S.lib.orgs.length + " организаций", "users")}${tile("#/lib/profiles", "Профили и шаблоны", "Базовый состав и отдельные требования заказчика", S.lib.profiles.length + " профиля", "tag")}</div><div class="flow-note"><b>Рабочая структура:</b> объект → система → акт. Схемы находятся в системе, паспорта — у материалов, протоколы — в испытаниях. В акте выбираются нужные связи, а том собирается из уже подготовленных разделов.</div></div>`;
};
V.p = (r) => {
  const p = proj(r[1]);
  if (!p) return V.home();
  const tab = r[2] || "overview",
    base = "#/p/" + p.id,
    C = check(p);
  let body = "";
  if (tab === "overview") {
    body = `<div class="homelead"><h2>Инженерные системы</h2><span class="sectionhint">Рабочие разделы и акты</span></div><div class="sysg">${sortedSys(
      p,
    )
      .map((s) => {
        const d = s.acts.filter((a) => a.status === "Готово").length;
        return `<a class="sc" href="#/s/${s.id}"><div class="row"><span class="code">${esc(s.code)}</span><span class="grow"></span>${s.scheme.file ? '<span class="pill p-g">Схемы есть</span>' : '<span class="small mut">Без схем</span>'}</div><div class="nm">${esc(s.name)}</div><div class="numline"><span><b>${s.acts.length}</b> актов</span><span><b>${usedMaterials(s).size}</b> материалов</span><span><b>${s.aik.length}</b> АИК</span></div><div class="prog"><i style="width:${s.acts.length ? Math.round((d / s.acts.length) * 100) : 0}%"></i></div><span class="small mut">${d} из ${s.acts.length} актов готово</span></a>`;
      })
      .join(
        "",
      )}<a class="sc new" href="#" data-a="newSystem" data-p="${p.id}">${ic("plus")}Добавить систему</a></div><div class="homelead"><h2>Общее по объекту</h2></div><div class="section-grid">${tile(base + "/general", "Общие разделы", "Организационные документы, ОЖР, геодезия и эксплуатация", "4 раздела", "folder")}${tile(base + "/mats", "Материалы объекта", "Материалы всех систем с паспортами и сертификатами", p.materials.length + " материалов", "box")}${tile("#/build/" + p.id, "Сборка томов", "Объектовый том, системы и комплект для эксплуатации", volumeList(p).length + " томов", "layers")}</div>`;
  } else if (["info", "mats", "ozhr", "check"].includes(tab))
    body = legacyBody(originalViews.p(r));
  else if (tab === "general")
    body = `<div class="section-grid">${tile(base + "/admin", "Организационные документы", "Приказы, доверенности, документы участников", p.admin.length + " документов", "users")}${tile(base + "/ozhr", "Общий журнал работ", "Записи или загруженный журнал", p.journals.length + " журналов", "stamp")}${tile(base + "/surveys", "Геодезия", "Исполнительные съёмки и геодезические материалы", p.surveys.length + " документов", "stamp")}${tile(base + "/operations", "Для эксплуатации", "Инструкции и документы для передачи эксплуатирующей организации", p.opsDocs.length + " документов", "doc")}</div>`;
  else if (["admin", "surveys", "operations"].includes(tab)) {
    const key = { admin: "admin", surveys: "surveys", operations: "opsDocs" }[
        tab
      ],
      title = {
        admin: "Организационные документы объекта",
        surveys: "Исполнительная геодезия",
        operations: "Документы для эксплуатации",
      }[tab];
    body = `<div class="route-head"><h2>${title}</h2></div>${objectRegister(p, key, title)}`;
  } else body = '<div class="empty">Выберите раздел объекта.</div>';
  return `<div class="page">${hdr(esc(p.name), esc(p.address || "") + " · " + esc(p.cipher || "шифр не заполнен"), B(ic("plus") + " Система", "newSystem", `data-p="${p.id}"`) + B(ic("layers") + " Сборка томов", "nav", `data-h="#/build/${p.id}"`, "pri"), '<a href="#/home">Объекты</a>')}${tabs(
    base,
    ["admin", "surveys", "operations", "ozhr"].includes(tab) ? "general" : tab,
    [
      ["overview", "Системы"],
      ["general", "Общие разделы"],
      ["mats", "Материалы объекта", p.materials.length],
      ["info", "Карточка объекта"],
      ["check", "Проверка", C.E.length + C.W.length],
    ],
  )}${
    ["admin", "surveys", "operations", "ozhr"].includes(tab)
      ? `<div class="stepnav"><a href="${base}/general">Общие разделы</a>${[
          ["admin", "Организационные"],
          ["ozhr", "ОЖР"],
          ["surveys", "Геодезия"],
          ["operations", "Эксплуатация"],
        ]
          .map(
            ([k, n]) =>
              `<a href="${base}/${k}" class="${k === tab ? "on" : ""}">${n}</a>`,
          )
          .join("")}</div>`
      : ""
  }${body}</div>`;
};
function objectRegister(p, key, title) {
  const arr = p[key];
  return `<div class="catalog-top"><span class="sectionhint">Только документы этого объекта.</span>${B(ic("plus") + " Добавить", "objectDocAdd", `data-p="${p.id}" data-key="${key}"`, "pri")}</div>${arr.length ? `<div class="file-grid">${arr.map((x) => `<div class="resource"><span class="sectionlabel">${esc(x.num || "Без номера")}</span><h3>${esc(x.name)}</h3><div class="filetitle">${esc(x.file || "Файл не загружен")}</div><div class="row">${B("Карточка", "objectDocEdit", `data-p="${p.id}" data-key="${key}" data-x="${x.id}"`, "sm")}${B(x.file ? "Заменить PDF" : "Загрузить PDF", "pickPdf", `data-ent="proj" data-id="${p.id}" data-p="${key}.#${x.id}"`, "sm")}${x.fileKey ? B("Открыть", "openBlob", `data-key="${x.fileKey}"`, "sm") : ""}<span class="grow"></span>${B(ic("trash"), "rowRm", `data-ent="proj" data-id="${p.id}" data-p="${key}" data-r="${x.id}" aria-label="Удалить документ"`, "sm icon ghost")}</div></div>`).join("")}</div>` : `<div class="demo-empty"><h3>В этом разделе пока нет записей</h3><p>Добавьте документ, укажите реквизиты и прикрепите файл.</p>${B("Добавить документ", "objectDocAdd", `data-p="${p.id}" data-key="${key}"`, "pri")}</div>`}`;
}
A.objectDocAdd = (d) => {
  if (!guard("obj:" + d.p)) return;
  const p = proj(d.p),
    x = {
      id: uid(),
      name: "Новый документ",
      num: "",
      date: today(),
      file: "",
      pages: 0,
    };
  p[d.key].push(x);
  save();
  A.objectDocEdit({ ...d, x: x.id });
};
A.objectDocEdit = (d) => {
  const p = proj(d.p),
    x = p[d.key].find((x) => x.id === d.x);
  modal(
    "Карточка документа",
    `<div class="g2">${F("Наименование", "proj", p.id, `${d.key}.#${x.id}.name`, x.name, { span: 1 })}${F("Номер", "proj", p.id, `${d.key}.#${x.id}.num`, x.num)}${F("Дата", "proj", p.id, `${d.key}.#${x.id}.date`, x.date, { type: "date" })}${F("Число страниц", "proj", p.id, `${d.key}.#${x.id}.pages`, x.pages, { type: "number" })}</div>`,
    [
      {
        l: "Готово",
        c: "pri",
        f: () => {
          save();
          render();
        },
      },
    ],
  );
};
V.s = (r) => {
  const c = ctx("sys", r[1]),
    s = c.o,
    p = c.p;
  if (!s) return V.home();
  const tab = r[2] || "overview",
    base = "#/s/" + s.id;
  let body = "";
  if (tab === "overview") {
    const done = s.acts.filter((a) => a.status === "Готово").length;
    body = `<div class="kpis"><div class="kpi"><div class="v">${s.acts.length}</div><div class="l">актов в системе</div></div><div class="kpi"><div class="v">${done}</div><div class="l">актов готово</div></div><div class="kpi"><div class="v">${resourceList(s).filter((x) => x.record.file).length}</div><div class="l">файлов схем</div></div><div class="kpi"><div class="v">${usedMaterials(s).size}</div><div class="l">материалов в работе</div></div></div><div class="section-grid">${tile(base + "/acts", "Акты", "Скрытые работы и ответственные конструкции", s.acts.length + " актов", "doc")}${tile(base + "/schemes", "Исполнительные схемы", "Комплект системы и отдельные схемы. Привязка листов к актам.", resourceList(s).length + " карточек", "stamp")}${tile(base + "/materials", "Материалы и паспорта", "Материалы этой системы, документы качества и применение", usedMaterials(s).size + " материалов", "box")}${tile(base + "/aik", "Входной контроль", "АИК по материалам и связи с актами", s.aik.length + " актов", "check")}${tile(base + "/trials", "Испытания и протоколы", "Протоколы, акты испытаний и их применение", s.trials.length + s.acts.reduce((n, a) => n + a.tests.length, 0) + " документов", "doc")}${tile(base + "/jr", "Специальные журналы", "Журналы системы и записи о выполнении работ", s.journals.length + " журналов", "stamp")}</div><div class="homelead"><h2>Подготовка комплекта</h2></div><div class="section-grid">${tile(base + "/subs", "Комплекты и подписанты", "Кому сдаём, какие правила применяем, кто подписывает", s.subprofiles.length + " комплекта", "users")}${tile("#/build/" + p.id + "/" + volumeList(p).find((v) => v.s?.id === s.id)?.key, "Сборка тома системы", "Порядок документов, реестр и контроль страниц", "Перейти к сборке", "layers")}${tile("#/p/" + p.id + "/check", "Проверка объекта", "Ошибки, отсутствующие файлы и реквизиты", "Открыть замечания", "check")}</div>`;
  } else if (tab === "schemes") body = schemeCatalog(p, s);
  else if (tab === "scheme") {
    body = schemeTab(p, s).replace(
      /<div class="alert al-b">[\s\S]*?<\/div>/,
      '<div class="flow-note">Это исходный комплект схем системы. В акте выбираются конкретные листы из него. Выбор не создаёт новый исходный файл.</div>',
    );
    body = body
      .replace("Штамп наложен", "Макет штампа настроен")
      .replace("Наложить штамп", "Предпросмотр штампа");
  } else if (tab === "materials") body = systemMaterials(p, s);
  else if (tab === "trials") body = trialCatalog(p, s);
  else if (["acts", "aik", "jr", "subs", "params"].includes(tab)) {
    body = legacyBody(originalViews.s(r));
    body = body.replace(/<div class="alert al-a">[\s\S]*?<\/div>/, "");
  } else body = '<div class="empty">Выберите раздел системы.</div>';
  return `<div class="page">${hdr(esc(s.code) + ' <span class="mut" style="font-weight:400">' + esc(s.name) + "</span>", esc(s.cipher) + " · " + esc(p.name), B(ic("plus") + " Новый акт", "newAct", `data-s="${s.id}"`, "pri"), `<a href="#/home">Объекты</a> / <a href="#/p/${p.id}">${esc(p.name)}</a>`)}${systemNav(s, tab === "scheme" ? "schemes" : tab)}${body}</div>`;
};
function schemeCatalog(p, s) {
  const list = resourceList(s);
  return `<div class="catalog-top"><div class="sectionhint">Исходные схемы хранятся здесь. В акте выбираются схема и листы.</div>${B(ic("plus") + " Отдельная схема", "sketchAdd", `data-s="${s.id}"`, "pri")}</div><div class="file-grid">${list
    .map((x) => {
      const used = s.acts.filter((a) =>
        a.schemeLinks.some((l) => l.id === x.id),
      );
      return `<div class="resource"><span class="sectionlabel">${x.kind === "system" ? "Комплект системы" : x.kind === "act" ? "Схема из акта " + x.owner.num : "Отдельная схема"}</span><h3>${esc(x.name)}</h3><div class="filetitle">${esc(x.record.file || "Файл не загружен")}</div><div class="row"><span class="pill ${x.record.file ? "p-n" : "p-a"}">${x.record.pages || 0} л.</span><span class="small mut">${used.length} связей с актами</span></div>${used.length ? `<div class="small mt">${used.map((a) => `<a href="#/a/${a.id}/schemes">${esc(a.num)}</a>`).join(" · ")}</div>` : ""}<div class="row">${x.kind === "system" ? B("Карточка и штамп", "nav", `data-h="#/s/${s.id}/scheme"`, "sm") + B(x.record.file ? "Заменить PDF" : "Загрузить PDF", "schemeFile", `data-s="${s.id}"`, "sm") : x.kind === "act" ? B("Открыть в акте", "nav", `data-h="#/a/${x.owner.id}/schemes"`, "sm") : B("Карточка", "sketchEdit", `data-s="${s.id}" data-x="${x.id}"`, "sm") + B(x.record.file ? "Заменить PDF" : "Загрузить PDF", "pickPdf", `data-ent="sys" data-id="${s.id}" data-p="sketches.#${x.id}"`, "sm")}${x.record.fileKey ? B("Открыть PDF", "openBlob", `data-key="${x.record.fileKey}"`, "sm") : ""}</div></div>`;
    })
    .join(
      "",
    )}</div><div class="flow-note"><b>Один источник — несколько актов.</b> Если к АОСР нужен лист из общего комплекта, выберите его в карточке акта. Отдельная отрисовка в программе для этого не требуется.</div>`;
}
function systemMaterials(p, s) {
  const ids = usedMaterials(s),
    list = p.materials.filter((m) => ids.has(m.id));
  return `<div class="catalog-top"><span class="sectionhint">Показаны материалы этой системы. Паспорта и сертификаты открываются в карточке материала.</span>${B(ic("plus") + " Выбрать материалы", "systemMatPick", `data-s="${s.id}"`, "pri")}</div>${
    list.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Материал</th><th>Документы качества</th><th>Применение</th><th>Входной контроль</th></tr></thead><tbody>${list
          .map((m) => {
            const as = s.acts.filter((a) => a.materials.includes(m.id)),
              ks = s.aik.filter((k) => k.materialId === m.id);
            return `<tr><td><a href="#/m/${m.id}"><b>${esc(mName(m))}</b></a><div class="t2">${esc(mF(m, "maker"))}</div></td><td>${
              mDocs(m).length
                ? mDocs(m)
                    .map((d) => `<span class="pill p-n">${esc(d.type)}</span>`)
                    .join(" ")
                : '<span class="pill p-a">Нет документов</span>'
            }</td><td>${as.map((a) => `<a href="#/a/${a.id}/mat">${esc(a.num)}</a>`).join("<br>") || "Назначен системе"}</td><td>${ks.map((k) => `<a href="#/k/${k.id}">${esc(k.num)}</a>`).join("<br>") || B("Создать АИК", "newAik", `data-s="${s.id}"`, "sm")}</td></tr>`;
          })
          .join("")}</tbody></table></div>`
      : '<div class="demo-empty"><h3>Материалы ещё не выбраны</h3><p>Выберите из материалов объекта. Материалы, указанные в актах и АИК, появятся здесь автоматически.</p></div>'
  }<div class="row mt">${B("Все материалы объекта", "nav", `data-h="#/p/${p.id}/mats"`)}</div>`;
}
A.systemMatPick = (d) => {
  const c = ctx("sys", d.s),
    s = c.o,
    p = c.p;
  modal(
    "Материалы системы " + s.code,
    `<div class="lst">${p.materials.map((m) => `<label><input class="system-mat-choice" type="checkbox" value="${m.id}" ${(s.materialIds || []).includes(m.id) ? "checked" : ""}><span>${esc(mName(m))}</span></label>`).join("")}</div><div class="small mut mt">Материалы, уже используемые в актах, сохранятся в списке независимо от выбора.</div>`,
    [
      { l: "Отмена" },
      {
        l: "Применить",
        c: "pri",
        f: () => {
          if (!guard("sys:" + s.id)) return false;
          s.materialIds = [
            ...document.querySelectorAll(".system-mat-choice:checked"),
          ].map((x) => x.value);
          commit("Выбраны материалы системы " + s.code, s);
        },
      },
    ],
    "wide",
  );
};
A.sketchAdd = (d) => {
  if (!guard("sys:" + d.s)) return;
  const s = getEnt("sys", d.s),
    x = ROWT.scheme(s);
  x.name = "Новая исполнительная схема";
  s.sketches.push(x);
  save();
  A.sketchEdit({ ...d, x: x.id });
};
A.sketchEdit = (d) => {
  const s = getEnt("sys", d.s),
    x = s.sketches.find((x) => x.id === d.x);
  modal(
    "Карточка исполнительной схемы",
    `<div class="g2">${F("Наименование", "sys", s.id, "sketches.#" + x.id + ".name", x.name, { span: 1 })}${F("Формат", "sys", s.id, "sketches.#" + x.id + ".format", x.format, { opts: FORMATS })}${F("Количество листов", "sys", s.id, "sketches.#" + x.id + ".pages", x.pages, { type: "number" })}${F("Шифр рабочей документации", "sys", s.id, "sketches.#" + x.id + ".rd", x.rd, { span: 1 })}</div><div class="small mut mt">Файл загружается в разделе «Схемы». Связи с актами задаются в карточке акта.</div>`,
    [
      {
        l: "Готово",
        c: "pri",
        f: () => {
          save();
          render();
        },
      },
    ],
  );
};
function trialCatalog(p, s) {
  const list = [
    ...s.trials.map((t) => ({ t, owner: null })),
    ...s.acts.flatMap((a) => a.tests.map((t) => ({ t, owner: a }))),
  ];
  return `<div class="catalog-top"><span class="sectionhint">Отдельный реестр испытаний этой системы.</span>${B(ic("plus") + " Протокол / испытание", "trialAdd", `data-s="${s.id}"`, "pri")}</div>${
    list.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th>Номер и дата</th><th>Файл</th><th>Связь с актом</th><th></th></tr></thead><tbody>${list
          .map(
            ({ t, owner }) =>
              `<tr><td><b>${esc(t.name || "Новое испытание")}</b></td><td>${esc(t.num || "—")}<br><span class="t2">${fmtD(t.date)}</span></td><td>${t.file ? esc(t.file) + '<div class="t2">' + t.pages + " л.</div>" : '<span class="pill p-a">Не загружен</span>'}</td><td>${
                owner
                  ? `<a href="#/a/${owner.id}/tests">${esc(owner.num)}</a>`
                  : s.acts
                      .filter((a) => a.testLinks.includes(t.id))
                      .map(
                        (a) => `<a href="#/a/${a.id}/tests">${esc(a.num)}</a>`,
                      )
                      .join("<br>") || '<span class="t2">Не привязан</span>'
              }</td><td>${owner ? B("Открыть", "nav", `data-h="#/a/${owner.id}/tests"`, "sm") : B("Карточка", "trialEdit", `data-s="${s.id}" data-x="${t.id}"`, "sm")}</td></tr>`,
          )
          .join("")}</tbody></table></div>`
      : '<div class="demo-empty"><h3>Испытаний пока нет</h3><p>Создайте протокол, заполните дату и номер, загрузите файл.</p></div>'
  }`;
}
A.trialAdd = (d) => {
  if (!guard("sys:" + d.s)) return;
  const s = getEnt("sys", d.s),
    x = ROWT.test(s);
  x.name = "Новое испытание";
  s.trials.push(x);
  save();
  A.trialEdit({ ...d, x: x.id });
};
A.trialEdit = (d) => {
  const s = getEnt("sys", d.s),
    x = s.trials.find((x) => x.id === d.x);
  modal(
    "Испытание / протокол",
    `<div class="g2">${F("Наименование", "sys", s.id, "trials.#" + x.id + ".name", x.name, { span: 1 })}${F("Номер", "sys", s.id, "trials.#" + x.id + ".num", x.num)}${F("Дата", "sys", s.id, "trials.#" + x.id + ".date", x.date, { type: "date" })}${F("Количество листов", "sys", s.id, "trials.#" + x.id + ".pages", x.pages, { type: "number" })}</div><div class="row mt">${B(x.file ? "Заменить PDF" : "Загрузить PDF", "pickPdf", `data-ent="sys" data-id="${s.id}" data-p="trials.#${x.id}"`)}${x.fileKey ? B("Открыть PDF", "openBlob", `data-key="${x.fileKey}"`) : ""}</div><div class="notice small mut mt">${esc(x.file || "Файл не загружен")}</div>`,
    [
      {
        l: "Готово",
        c: "pri",
        f: () => {
          save();
          render();
        },
      },
    ],
  );
};
V.a = (r) => {
  const c = ctx("act", r[1]),
    a = c.o,
    s = c.s,
    p = c.p;
  if (!a) return V.home();
  const tab = r[2] || "main",
    base = "#/a/" + a.id;
  let body = "";
  if (["main", "mat", "prev"].includes(tab))
    body = legacyBody(originalViews.a(r));
  else if (tab === "schemes") body = actSchemes(a, s);
  else if (tab === "tests") body = actTests(a, s);
  else if (tab === "photos")
    body = `<div class="card"><h3>Фотофиксация работ по ${esc(a.num)}</h3>${photoEditor(a)}</div>`;
  else if (tab === "scan") {
    body = `<div class="card"><h3>Подписанный оригинал / скан</h3>${fileBox(a.scan?.file, a.scan?.pages, B(a.scan?.file ? "Заменить скан" : "Загрузить скан", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="scan"`))}${a.scan?.fileKey ? '<div class="row mt">' + B("Открыть PDF", "openBlob", `data-key="${a.scan.fileKey}"`) + "</div>" : ""}<div class="flow-note">При подготовке состава тома скан учитывается вместо сформированной формы акта. Статус «Готово» отмечается после ручной проверки реквизитов и подписей.</div></div>`;
  } else if (tab === "att" || tab === "files") body = actSchemes(a, s);
  return `<div class="page actbody">${hdr(esc(a.num), esc(cut(a.works || "Новый акт", 100)), B(ic("copy") + " Дублировать", "dup", `data-id="${a.id}"`) + B(ic("trash"), "del", `data-ent="act" data-id="${a.id}" title="Удалить акт"`, "icon"), `<a href="#/home">Объекты</a> / <a href="#/p/${p.id}">${esc(p.name)}</a> / <a href="#/s/${s.id}/acts">${esc(s.code)} · Акты</a>`)}${tabs(
    base,
    tab === "att" ? "schemes" : tab,
    [
      ["main", "Содержание"],
      ["mat", "Материалы", a.materials.length],
      ["schemes", "Схемы к акту", a.schemes.length + a.schemeLinks.length],
      ["tests", "Испытания", a.tests.length + a.testLinks.length],
      ["photos", "Фото", a.photos.length],
      ["scan", "Подписанный акт", a.scan?.file ? 1 : ""],
      ["prev", "Предпросмотр"],
    ],
  )}${body}</div>`;
};
function actSchemes(a, s) {
  return `<div class="card"><h3>Листы из комплекта системы<span class="r">${B(ic("link") + " Выбрать схему и листы", "linkScheme", `data-id="${a.id}"`, "sm pri")}</span></h3>${
    linkedSchemes(a, s)
      .map(
        ({ link, item }) =>
          `<div class="sheet-link">${ic("stamp")}<div class="grow"><b>${esc(item?.name || "Источник удалён")}</b><div class="small mut">${esc(item?.record.file || "Файл отсутствует")} · листы ${link.from}–${link.to}</div></div>${item?.record.fileKey ? B("Открыть PDF", "openBlob", `data-key="${item.record.fileKey}"`, "sm") : ""}${B("Источник", "nav", `data-h="#/s/${s.id}/schemes"`, "sm")}${B(ic("trash"), "unlinkScheme", `data-id="${a.id}" data-x="${link.id}" aria-label="Отвязать схему"`, "sm icon ghost")}</div>`,
      )
      .join("") ||
    '<div class="small mut">Связи ещё не выбраны. Прикрепите к акту нужную схему или листы общего комплекта.</div>'
  }<div class="flow-note">Связь хранит источник и номера листов. Один лист можно использовать в нескольких актах; исходный PDF остаётся один.</div></div><div class="card"><h3>Отдельные схемы только к этому акту<span class="r">${B(ic("plus") + " Добавить", "rowAdd", `data-ent="act" data-id="${a.id}" data-p="schemes" data-k="scheme"`, "sm")}</span></h3>${a.schemes.length ? `<div class="file-grid">${a.schemes.map((x) => `<div class="resource">${F("Наименование", "act", a.id, "schemes.#" + x.id + ".name", x.name)}${fileBox(x.file, x.pages, "")}<div class="row">${B(x.file ? "Заменить PDF" : "Загрузить PDF", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="schemes.#${x.id}"`, "sm")}${x.fileKey ? B("Открыть", "openBlob", `data-key="${x.fileKey}"`, "sm") : ""}${B("Макет штампа", "ownPrev", `data-id="${a.id}" data-x="${x.id}"`, "sm")}${B(ic("trash"), "rowRm", `data-ent="act" data-id="${a.id}" data-p="schemes" data-r="${x.id}" title="Удалить"`, "sm icon ghost")}</div></div>`).join("")}</div>` : '<div class="small mut">Отдельных схем нет. Этот раздел нужен, если для акта подготовлен самостоятельный файл.</div>'}</div>`;
}
A.linkScheme = (d) => {
  const c = ctx("act", d.id),
    a = c.o,
    s = c.s,
    L = resourceList(s).filter((x) => x.record.file && x.owner?.id !== a.id);
  if (!L.length) {
    toast("Сначала загрузите схему в раздел системы «Схемы».");
    return;
  }
  modal(
    "Схема и листы к " + a.num,
    `<label class="fld"><span>Исходная схема</span><select id="scheme-link-source">${L.map((x) => `<option value="${x.id}">${esc(x.name)} · ${x.record.pages} л.</option>`).join("")}</select></label><div class="g2 mt"><label class="fld"><span>С листа</span><input id="scheme-link-from" type="number" min="1" value="1"></label><label class="fld"><span>По лист</span><input id="scheme-link-to" type="number" min="1" value="1"></label></div><div class="small mut mt">Номера — порядковые страницы исходного PDF. Сверьте их с обозначениями листов схемы.</div>`,
    [
      { l: "Отмена" },
      {
        l: "Привязать",
        c: "pri",
        f: () => {
          if (!guard("sys:" + s.id)) return false;
          const id = $("#scheme-link-source").value,
            item = L.find((x) => x.id === id),
            from = Number($("#scheme-link-from").value),
            to = Number($("#scheme-link-to").value);
          if (
            !Number.isInteger(from) ||
            !Number.isInteger(to) ||
            from < 1 ||
            to < from ||
            to > item.record.pages
          ) {
            toast("Укажите диапазон в пределах исходного файла.");
            return false;
          }
          const old = a.schemeLinks.find((l) => l.id === id);
          if (old) Object.assign(old, { from, to });
          else a.schemeLinks.push({ id, from, to });
          commit("Привязаны листы схемы к " + a.num, a);
        },
      },
    ],
  );
};
A.unlinkScheme = (d) => {
  if (!guard(entKey("act", d.id))) return;
  const a = getEnt("act", d.id);
  a.schemeLinks = a.schemeLinks.filter((x) => x.id !== d.x);
  commit("Убрана связь схемы с " + a.num, a);
};
function actTests(a, s) {
  return `<div class="card"><h3>Испытания из реестра системы<span class="r">${B("Выбрать протоколы", "linkTrial", `data-id="${a.id}"`, "sm")}</span></h3>${
    a.testLinks
      .map((id) => {
        const t = s.trials.find((t) => t.id === id);
        return `<div class="sheet-link">${ic("doc")}<div class="grow"><b>${esc(t?.name || "Источник удалён")}</b><div class="small mut">${esc(t?.num || "—")} · ${fmtD(t?.date)}</div></div>${t?.fileKey ? B("Открыть", "openBlob", `data-key="${t.fileKey}"`, "sm") : ""}${B("Источник", "nav", `data-h="#/s/${s.id}/trials"`, "sm")}</div>`;
      })
      .join("") ||
    '<div class="small mut">Испытания из реестра не выбраны.</div>'
  }</div><div class="card"><h3>Отдельные испытания к акту<span class="r">${B(ic("plus") + " Добавить", "rowAdd", `data-ent="act" data-id="${a.id}" data-p="tests" data-k="test"`, "sm")}</span></h3>${a.tests.map((t) => `<div class="resource" style="margin-bottom:15px"><div class="g2">${F("Наименование", "act", a.id, "tests.#" + t.id + ".name", t.name, { span: 1 })}${F("Номер", "act", a.id, "tests.#" + t.id + ".num", t.num)}${F("Дата", "act", a.id, "tests.#" + t.id + ".date", t.date, { type: "date" })}</div>${fileBox(t.file, t.pages, "")}<div class="row mt">${B(t.file ? "Заменить PDF" : "Загрузить PDF", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="tests.#${t.id}"`, "sm")}${t.fileKey ? B("Открыть", "openBlob", `data-key="${t.fileKey}"`, "sm") : ""}${B(ic("trash"), "rowRm", `data-ent="act" data-id="${a.id}" data-p="tests" data-r="${t.id}" title="Удалить"`, "sm icon ghost")}</div></div>`).join("") || '<div class="small mut">Отдельных испытаний нет.</div>'}</div>`;
}
A.linkTrial = (d) => {
  const c = ctx("act", d.id),
    a = c.o,
    s = c.s;
  modal(
    "Испытания к " + a.num,
    `<div class="lst">${s.trials.map((t) => `<label><input class="trial-choice" type="checkbox" value="${t.id}" ${a.testLinks.includes(t.id) ? "checked" : ""}><span>${esc(t.name)} · ${esc(t.num)}</span></label>`).join("") || '<div class="empty">В реестре системы пока нет протоколов.</div>'}</div>`,
    [
      { l: "Отмена" },
      {
        l: "Применить",
        c: "pri",
        f: () => {
          if (!guard("sys:" + s.id)) return false;
          a.testLinks = [
            ...document.querySelectorAll(".trial-choice:checked"),
          ].map((x) => x.value);
          commit("Выбраны испытания к " + a.num, a);
        },
      },
    ],
  );
};
function actAttachmentEntries(a, s) {
  const entries = [],
    owned = new Set((a.schemes || []).map((x) => x.id)),
    linked = new Map();
  const scheme = (record, pages, fallback) => ({
    schemeId: record === s.scheme ? "system" : record.id,
    name:
      "Исполнительная схема" +
      (record.num ? " № " + record.num : "") +
      " «" +
      (record.name || fallback || "Название не указано") +
      "»",
    pages,
  });
  for (const { link, item } of linkedSchemes(a, s)) {
    if (!item || owned.has(item.id)) continue;
    if (!linked.has(item.id)) linked.set(item.id, { item, pages: new Set() });
    for (let n = Number(link.from); n <= Number(link.to); n++)
      linked.get(item.id).pages.add(n);
  }
  for (const { item, pages } of linked.values())
    entries.push(scheme(item.record, pages.size, item.name));
  for (const x of a.schemes || [])
    entries.push(scheme(x, Number(x.pages) || 0));
  const tests = [
    ...(a.tests || []),
    ...(a.testLinks || [])
      .map((id) => s.trials.find((t) => t.id === id))
      .filter(Boolean),
  ];
  const seen = new Set();
  for (const t of tests) {
    if (t.id && seen.has(t.id)) continue;
    seen.add(t.id);
    entries.push({
      name:
        (t.name || "Протокол испытаний") +
        (t.num ? " № " + t.num : "") +
        (t.date ? " от " + fmtD(t.date) : ""),
      pages: Number(t.pages) || 0,
    });
  }
  const photos = photoSheets(a);
  if (photos)
    entries.push({
      name: "Фототаблица к " + a.type + " № " + a.num,
      pages: photos,
    });
  return entries;
}
const oldAppsText = appsText;
appsText = (a, s) =>
  actAttachmentEntries(a, s)
    .map((x, i) => i + 1 + ". " + x.name + ", " + (x.pages || "?") + " л.")
    .join("\n") || "Не выбраны";

const oldAosr = aosrHtml;
aosrHtml = (a, p, s, sp) => {
  const copy = {
    ...a,
    tests: [
      ...a.tests,
      ...a.testLinks
        .map((id) => s.trials.find((t) => t.id === id))
        .filter(Boolean),
    ],
    schemes: [
      ...a.schemes,
      ...linkedSchemes(a, s)
        .filter((x) => x.item)
        .map(({ link, item }) => ({
          ...item.record,
          pages: link.to - link.from + 1,
        })),
    ],
    schemeLinks: [],
    testLinks: [],
  };
  let html = oldAosr(copy, p, { ...s, scheme: { ...s.scheme, file: "" } }, sp);
  return html.replace(
    /<div>Приложения:[\s\S]*?<\/div>/,
    `<div>Приложения:<br>${esc(appsText(a, s)).replace(/\n/g, "<br>")}</div>`,
  );
};
const oldBlocks = blocksFor;
blocksFor = (p, vol) => {
  const BL = oldBlocks(p, vol);
  if (vol.kind === "T1") {
    const b = BL.find((b) => b.key === "orders");
    if (b)
      b.items = p.admin.map((x) => ({
        id: "admin" + x.id,
        type: "Организационный документ",
        name: x.name,
        nd: "№ " + x.num + " от " + fmtD(x.date),
        pages: x.pages || 1,
        file: x.file,
        ref: "#/p/" + p.id + "/admin",
      }));
  }
  if (vol.s) {
    const s = vol.s,
      b = BL.find((b) => b.key === "schemes"),
      t = BL.find((b) => b.key === "tests");
    if (b) {
      s.sketches.forEach((x) =>
        b.items.push({
          id: "sk" + x.id,
          type: "Исполнительная схема",
          name: x.name,
          nd: "система " + s.code,
          pages: x.pages || 1,
          file: x.file,
          ref: "#/s/" + s.id + "/schemes",
        }),
      );
      const cfg = S.volCfg[p.id + "|" + vol.key];
      if (cfg?.docs?.schemes) {
        const order = cfg.docs.schemes;
        b.items.sort(
          (x, y) =>
            (order.includes(x.id) ? order.indexOf(x.id) : 1e6) -
            (order.includes(y.id) ? order.indexOf(y.id) : 1e6),
        );
      }
    }
    if (t) {
      s.trials.forEach((x) =>
        t.items.push({
          id: "trial" + x.id,
          type: "Испытание / протокол",
          name: x.name,
          nd: "№ " + x.num + " от " + fmtD(x.date),
          pages: x.pages || 1,
          file: x.file,
          ref: "#/s/" + s.id + "/trials",
        }),
      );
    }
  }
  const count = BL.filter((b) => !b.off && !b.auto).reduce(
      (n, b) => n + b.items.length,
      0,
    ),
    reg = BL.find((b) => b.auto);
  if (reg) reg.items[0].pages = Math.max(1, Math.ceil((count + 1) / 22));
  return BL;
};
const oldCheck = check;
check = (p) => {
  const C = oldCheck(p);
  p.systems.forEach((s) => {
    s.sketches.forEach((x) => {
      if (!x.file)
        C.W.push({
          t: s.code + ": не загружена схема «" + x.name + "»",
          l: "#/s/" + s.id + "/schemes",
        });
    });
    s.trials.forEach((t) => {
      if (!t.file)
        C.E.push({
          t: s.code + ": у испытания «" + t.name + "» нет файла",
          l: "#/s/" + s.id + "/trials",
        });
    });
    s.acts.forEach((a) => {
      linkedSchemes(a, s).forEach(({ link, item }) => {
        if (!item)
          C.E.push({
            t: a.num + ": удалён источник схемы",
            l: "#/a/" + a.id + "/schemes",
          });
        else if (!item.record.file)
          C.E.push({
            t: a.num + ": у связанной схемы нет файла",
            l: "#/a/" + a.id + "/schemes",
          });
        else if (link.to > item.record.pages)
          C.E.push({
            t: a.num + ": диапазон листов выходит за пределы схемы",
            l: "#/a/" + a.id + "/schemes",
          });
      });
      a.testLinks.forEach((id) => {
        if (!s.trials.some((t) => t.id === id))
          C.E.push({
            t: a.num + ": удалён связанный протокол",
            l: "#/a/" + a.id + "/tests",
          });
      });
    });
  });
  C.E.forEach(
    (x) =>
      (x.l = x.l.replace(
        "/att",
        x.t.includes("у схемы") ? "/schemes" : "/tests",
      )),
  );
  return C;
};

A.assemblyJson = () => {
  const { p, vol } = curVol(),
    R = registry(p, vol);
  download(
    slug(p.name + "_" + vol.short) + "_состав.json",
    JSON.stringify(
      {
        object: p.name,
        volume: vol.title,
        generated: nowStr(),
        profile: vol.sp ? prof(vol.sp.profileId)?.name : null,
        rows: R.rows,
        links: vol.s?.acts.map((a) => ({
          act: a.num,
          schemes: a.schemeLinks,
          tests: a.testLinks,
        })),
        checks: check(p),
      },
      null,
      2,
    ),
    "application/json",
  );
  toast("Состав тома выгружен.");
};
const oldSettings = V.settings;
V.settings = (r) => {
  if (r[1] && r[1] !== "general") return oldSettings(r);
  return `<div class="page">${hdr("Сохранение и настройки", "Карточки сохраняются локально в этом браузере. Используйте JSON для переноса проекта.")}${tabs(
    "#/settings",
    "general",
    [
      ["general", "Основное"],
      ["trash", "Корзина", S.trash.length],
    ],
  )}<div class="card"><h3>Проект</h3><div class="row">${B(ic("download") + " Сохранить проект JSON", "exportJson", "", "pri")}${B(ic("imp") + " Открыть проект JSON", "importJson")}</div><div class="flow-note">JSON содержит карточки и связи. PDF хранятся отдельно в этом браузере; для передачи сохраняйте исходные файлы отдельно.</div></div><div class="card"><h3>Пользователь и режим</h3><div class="g2">${F("Имя пользователя", "app", "", "user", APP.user, { rr: 1 })}<div class="fld"><span>Режим работы</span>${B(S.ui.ro ? "Включить редактирование" : "Только просмотр", "roToggle")}</div></div></div><div class="card"><h3>Демонстрационные данные</h3><div class="small mut mb">Записи показывают структуру программы. Имена демо-файлов не содержат настоящих PDF.</div>${B("Восстановить демо-данные", "resetDemo", "", "dng")}</div></div>`;
};
const oldJournalView = V.j;
V.j = (r) =>
  oldJournalView(r).replace(
    /<button[^>]*data-a="stub"[^>]*>[^<]*<\/button>/g,
    B("Скачать журнал HTML", "journalHtml", `data-id="${r[1]}"`),
  );
A.journalHtml = (d) => {
  const j = ctx("jr", d.id).o;
  if (!j) return;
  const html = `<h2>${esc(j.name)}</h2><table><tr><th>№</th>${j.cols.map((c) => "<th>" + esc(c) + "</th>").join("")}</tr>${j.rows.map((r, i) => "<tr><td>" + (i + 1) + "</td>" + j.cols.map((c, k) => "<td>" + esc(r.c[k] || "") + "</td>").join("") + "</tr>").join("")}</table>`;
  download(
    slug(j.name) + ".html",
    exportPage(j.name, html),
    "text/html;charset=utf-8",
  );
};
function exportPage(title, body) {
  return (
    '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>' +
    esc(title) +
    '</title><style>body{font:14px/1.45 "Times New Roman",serif;max-width:800px;margin:35px auto;padding:20px}table{width:100%;border-collapse:collapse}th,td{border:1px solid #444;padding:7px}.pl{border-bottom:1px solid #333;min-height:18px}.pc{font-size:10px;color:#555;text-align:center;margin-bottom:8px}h2,.c{text-align:center}.miss{color:#c00}</style></head><body>' +
    body +
    "</body></html>"
  );
}
A.actHtml = (d) => {
  const c = ctx("act", d.id),
    a = c.o,
    sp = spOf(c.s, a.subs[0]);
  if (!sp) return toast("Выберите комплект и подписантов.");
  download(
    slug(a.num) + ".html",
    exportPage(a.num, aosrHtml(a, c.p, c.s, sp)),
    "text/html;charset=utf-8",
  );
};
A.stampApply = (d) => {
  const s = getEnt("sys", d.s);
  modal(
    "Макет штампа — " + s.code,
    '<div class="small mut">Настройки макета сохранены. Наложение на исходный PDF в HTML-прототипе не выполняется.</div>',
    [{ l: "Готово", c: "pri" }],
  );
  save();
};
const blobCache = new Map();
let blobDbPromise;
function blobDb() {
  if (!window.indexedDB) return Promise.reject(Error("IndexedDB недоступен"));
  if (!blobDbPromise)
    blobDbPromise = new Promise((res, rej) => {
      const req = indexedDB.open("stroiid-full-files-v1", 1);
      req.onupgradeneeded = () => req.result.createObjectStore("files");
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
  return blobDbPromise;
}
async function keepFile(file) {
  const key = "f" + uid() + Date.now();
  blobCache.set(key, file);
  try {
    const db = await blobDb();
    await new Promise((res, rej) => {
      const tx = db.transaction("files", "readwrite");
      tx.objectStore("files").put(file, key);
      tx.oncomplete = res;
      tx.onerror = () => rej(tx.error);
    });
    return key;
  } catch (e) {
    toast(
      "Файл доступен только до закрытия страницы: браузер не разрешил сохранение.",
    );
    return key;
  }
}
async function getFile(key) {
  if (blobCache.has(key)) return blobCache.get(key);
  try {
    const db = await blobDb();
    return await new Promise((res, rej) => {
      const req = db.transaction("files").objectStore("files").get(key);
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
  } catch {
    return null;
  }
}
A.openBlob = async (d) => {
  const f = await getFile(d.key);
  if (!f)
    return toast(
      "Исходный файл недоступен в этом браузере. Загрузите его снова.",
    );
  const url = URL.createObjectURL(f);
  const w = window.open(url, "_blank", "noopener");
  if (!w) {
    download(f.name || "document.pdf", f, "application/pdf");
  }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
};
function askFilePages(t, o, file, onSaved) {
  modal(
    "Количество страниц",
    `<div class="small mb">Файл: <b>${esc(file.name)}</b></div><label class="fld"><span>Укажите число страниц исходного PDF</span><input id="uploaded-pages" type="number" min="1" step="1" value="${t.pages || 1}"></label><div class="small mut mt">Автоматическое чтение страниц PDF в этом прототипе отключено. Проверьте число листов в просмотрщике.</div>`,
    [
      {
        l: "Закрыть",
        f: () => {
          save();
          render();
        },
      },
      {
        l: "Сохранить",
        c: "pri",
        f: () => {
          const n = Number($("#uploaded-pages").value);
          if (!Number.isInteger(n) || n < 1) {
            toast("Введите целое положительное число.");
            return false;
          }
          t.pages = n;
          if (onSaved) onSaved();
          commit("Загружен PDF «" + file.name + "»", o);
        },
      },
    ],
  );
}
A.pickPdf = async (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  const [f] = await pickFiles(".pdf,application/pdf");
  if (!f) return;
  const o = getEnt(d.ent, d.id),
    t = d.p ? getPath(o, d.p) : o;
  if (!t) return;
  t.file = f.name;
  t.fileKey = await keepFile(f);
  t.pages = 0;
  save();
  askFilePages(t, o, f);
};
A.schemeFile = async (d) => {
  if (!guard("sys:" + d.s)) return;
  const [f] = await pickFiles(".pdf,application/pdf");
  if (!f) return;
  const s = getEnt("sys", d.s),
    sc = s.scheme;
  sc.file = f.name;
  sc.fileKey = await keepFile(f);
  sc.pages = 0;
  sc.stamped = false;
  sc.updated = nowStr();
  sc.updatedBy = APP.user;
  save();
  askFilePages(sc, s, f);
};
A.fileOpen = (d) => {
  const name = String(d.path || "")
    .split(/[\\/]/)
    .pop();
  const refs = [];
  function scan(x) {
    if (!x || typeof x !== "object") return;
    if (x.file === name && x.fileKey) refs.push(x.fileKey);
    Object.values(x).forEach((v) => {
      if (v && typeof v === "object") scan(v);
    });
  }
  scan(S);
  const keys = [...new Set(refs)];
  if (keys.length === 1) A.openBlob({ key: keys[0] });
  else
    toast(
      keys.length
        ? "Откройте нужную карточку: несколько файлов с таким именем."
        : "Это имя демонстрационного файла. Загрузите реальный PDF для просмотра.",
    );
};
A.showInFolder = () =>
  toast(
    "В HTML файлы открываются через карточки. Доступа к папкам Windows у страницы нет.",
  );
A.stub = (d) =>
  toast(
    (d.t || "Операция") +
      " требует обработки PDF или DOCX в полноценном приложении.",
  );
const originalCsv = csv;
csv = (rows) =>
  originalCsv(
    rows.map((row) =>
      row.map((v) =>
        typeof v === "string" && /^[=+@\-\t\r]/.test(v) ? "'" + v : v,
      ),
    ),
  );
const originalRenderWorkspace = render;
render = function () {
  ensureWorkspace();
  originalRenderWorkspace();
  const content = $("#content");
  if (content) {
    content.innerHTML = content.innerHTML
      .replace(/Подпрофили/g, "Комплекты")
      .replace(/подпрофил[ьяеоу]/g, "комплекта")
      .replace(/При сборке тома/g, "При подготовке состава тома")
      .replace(
        /Сборка тома будет заблокирована/g,
        "Подготовка комплекта ограничена",
      )
      .replace(
        /Комплект готов к сборке\./g,
        "По карточкам комплект прошёл проверку.",
      );
    const r = route();
    if (r[0] === "a" && r[2] === "prev") {
      content.querySelectorAll('[data-a="stub"]').forEach((el) => {
        el.dataset.a = "actHtml";
        el.dataset.id = r[1];
        el.textContent = "Скачать акт HTML";
      });
    }
  }
};
// JSON imports retain original schema compatibility and initialize new registers.
A.importJson = async () => {
  if (!guard(null)) return;
  const [f] = await pickFiles(".json");
  if (!f) return;
  try {
    const d = JSON.parse(await f.text());
    if (
      d.meta?.v !== 30 ||
      !Array.isArray(d.projects) ||
      !d.lib ||
      !Array.isArray(d.lib.orgs) ||
      !Array.isArray(d.lib.people) ||
      !Array.isArray(d.lib.base) ||
      !Array.isArray(d.lib.profiles) ||
      !Array.isArray(d.lib.templates)
    )
      throw Error("неверный формат");
    for (const p of d.projects) {
      if (
        !Array.isArray(p.systems) ||
        !Array.isArray(p.materials) ||
        !Array.isArray(p.journals) ||
        !Array.isArray(p.surveys) ||
        !Array.isArray(p.opsDocs)
      )
        throw Error("неполная структура объекта");
      for (const s of p.systems)
        if (
          !s.scheme ||
          !Array.isArray(s.acts) ||
          !Array.isArray(s.aik) ||
          !Array.isArray(s.journals) ||
          !Array.isArray(s.subprofiles)
        )
          throw Error("неполная структура системы");
    }
    d.locks = {};
    d.ui = S.ui;
    d.trash = d.trash || [];
    d.history = d.history || [];
    d.volCfg = d.volCfg || {};
    S = d;
    IX = null;
    ensureWorkspace();
    logH("Открыт проект " + f.name);
    save();
    go("#/home");
    render();
    toast("Проект открыт. Файлы из другого браузера нужно загрузить отдельно.");
  } catch (e) {
    toast("Проект не открыт: " + e.message);
  }
};
// Agent navigation uses the same contextual workspace as the visible UI.
if (document.modelContext?.registerTool) {
  const abort = new AbortController();
  for (const tool of [
    {
      name: "read_stroiid_structure",
      description: "Read objects and their systems without changing data.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute(input) {
        if (!input || Object.keys(input).length)
          throw Error("No arguments expected");
        return S.projects.map((p) => ({
          id: p.id,
          name: p.name,
          systems: p.systems.map((s) => ({
            id: s.id,
            code: s.code,
            acts: s.acts.length,
            schemes: resourceList(s).length,
            materials: usedMaterials(s).size,
          })),
        }));
      },
    },
    {
      name: "open_stroiid_system_section",
      description:
        "Open a specialized register inside the selected engineering system.",
      inputSchema: {
        type: "object",
        properties: {
          systemId: { type: "string" },
          section: {
            type: "string",
            enum: [
              "overview",
              "acts",
              "schemes",
              "materials",
              "aik",
              "trials",
              "jr",
            ],
          },
        },
        required: ["systemId", "section"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false },
      execute(input) {
        if (
          !input ||
          Object.keys(input).some(
            (k) => !["systemId", "section"].includes(k),
          ) ||
          ![
            "overview",
            "acts",
            "schemes",
            "materials",
            "aik",
            "trials",
            "jr",
          ].includes(input.section) ||
          !getEnt("sys", input.systemId)
        )
          throw Error("Unknown system or section");
        go("#/s/" + input.systemId + "/" + input.section);
        render();
        return { system: input.systemId, section: input.section };
      },
    },
  ]) {
    try {
      Promise.resolve(
        document.modelContext.registerTool(tool, { signal: abort.signal }),
      ).catch(() => {});
    } catch {}
  }
  window.addEventListener("pagehide", () => abort.abort(), { once: true });
}
// Complete page-count checks after uploads and when an original is replaced.
const checkWithLinks = check;
check = (p) => {
  const C = checkWithLinks(p);
  const test = (x, label, l) => {
    if (x.file && (!Number.isInteger(Number(x.pages)) || Number(x.pages) < 1))
      C.W.push({ t: label + ": уточните число страниц исходного файла", l });
  };
  p.admin.forEach((x) => test(x, x.name, "#/p/" + p.id + "/admin"));
  p.systems.forEach((s) => {
    test(s.scheme, s.code + " · комплект схем", "#/s/" + s.id + "/scheme");
    s.sketches.forEach((x) => test(x, x.name, "#/s/" + s.id + "/schemes"));
    s.trials.forEach((x) => test(x, x.name, "#/s/" + s.id + "/trials"));
    s.acts.forEach((a) => {
      a.schemes.forEach((x) =>
        test(x, a.num + " · " + x.name, "#/a/" + a.id + "/schemes"),
      );
      a.tests.forEach((x) =>
        test(x, a.num + " · " + x.name, "#/a/" + a.id + "/tests"),
      );
      if (a.scan) test(a.scan, a.num + " · скан", "#/a/" + a.id + "/scan");
    });
  });
  return C;
};
// Seed contextual examples; user-created and imported acts require explicit links.
const originalSeedFull = seed;
seed = function () {
  const d = originalSeedFull();
  d.meta.iaVersion = 4;
  d.projects.forEach((p, i) => {
    p.admin =
      i === 0
        ? d.lib.orders.map((x) => ({ ...clone(x), id: "adm" + uid() }))
        : [];
    p.systems.forEach((s) => {
      s.sketches = [];
      s.trials = [];
      s.materialIds = [];
      s.acts.forEach((a, j) => {
        a.schemeLinks =
          s.scheme.file && j < 2 ? [{ id: "system", from: 1, to: 1 }] : [];
        a.testLinks = [];
      });
    });
  });
  return d;
};
// New system sources obey the saved item order after all registers are merged.
const mergedBlocks = blocksFor;
blocksFor = (p, vol) => {
  const BL = mergedBlocks(p, vol),
    cfg = S.volCfg[p.id + "|" + vol.key];
  for (const b of BL) {
    const order = cfg?.docs?.[b.key];
    if (order)
      b.items.sort(
        (x, y) =>
          (order.includes(x.id) ? order.indexOf(x.id) : 1e6) -
          (order.includes(y.id) ? order.indexOf(y.id) : 1e6),
      );
  }
  return BL;
};
