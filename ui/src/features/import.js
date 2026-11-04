/* ---------- первый запуск и выбор базы ---------- */
V.welcome =
  () => `<div class="start"><div class="row" style="gap:14px;margin-bottom:28px">${LOGO}<div><div style="font-size:22px;font-weight:650">СтройИД</div><div class="mut">Исполнительная документация</div></div></div>
 <div class="card"><h3>Первый запуск на этом компьютере</h3><div class="mut small mb">Укажите имя инженера и название компьютера. Пароль не нужен: доступ к данным определяется тем, кому открыта папка на Яндекс Диске.</div>
 <div class="g2"><label class="fld"><span>Фамилия и инициалы <b class="req">*</b></span><input id="w-user" placeholder="Например, Иванов И. И." value="${esc(APP.user)}"></label><label class="fld"><span>Компьютер</span><input id="w-pc" value="${esc(APP.pc)}"></label></div>
 <div class="row mt" style="margin-top:16px">${B("Продолжить", "welcomeSave", "", "pri")}</div></div><div class="small mut">Эти данные хранятся на компьютере, а не в базе.</div></div>`;
V.start =
  () => `<div class="start"><div class="row" style="gap:14px;margin-bottom:28px">${LOGO}<div><div style="font-size:22px;font-weight:650">СтройИД</div><div class="mut">Исполнительная документация</div></div></div>
 <h1 style="margin-bottom:6px">Выберите базу</h1><div class="mut" style="margin-bottom:18px">База — это папка на Яндекс Диске. Программа работает с ней как с обычной папкой на компьютере, а синхронизацию с коллегами делает клиент Яндекс Диска. Работать можно и без интернета.</div>
 <div class="row mb">${B(ic("folder") + "Открыть папку базы…", "baseOpenDlg", "", "pri")}${B(ic("plus") + "Создать новую базу…", "baseCreateDlg")}</div>
 ${APP.recent.length ? `<div class="card" style="padding:0"><h3 style="padding:14px 16px 4px">Недавние базы</h3>${APP.recent.map((r) => `<div class="msg" data-a="baseOpen" data-path="${esc(r.path)}">${ic("folder", "ic fxd")}<span class="grow" style="min-width:0"><b style="font-weight:600">${esc(r.name)}</b><div class="small mut">${esc(r.path)}</div></span><span class="small mut">${esc(r.last || "")}</span>${B("×", "baseForget", `data-path="${esc(r.path)}" title="Убрать из списка"`, "sm icon ghost")}</div>`).join("")}</div>` : ""}
 <div class="small mut mt">Вы: ${esc(APP.user)} · ${esc(APP.pc)} — <a href="#" data-a="welcomeReset">изменить</a></div></div>`;
A.welcomeSave = () => {
  const u = $("#w-user").value.trim();
  if (!u) {
    toast("Укажите фамилию и инициалы");
    return;
  }
  APP.user = u;
  APP.pc = $("#w-pc").value.trim() || "PC-01";
  saveApp();
  render();
};
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.target.id === "w-user" || e.target.id === "w-pc"))
    A.welcomeSave();
});
A.welcomeReset = () => {
  APP.user = "";
  saveApp();
  render();
};
A.baseOpen = (d) => {
  if (openBase(d.path)) {
    go("#/home");
    render();
    return;
  }
  modal(
    "Папка недоступна",
    `<div class="alert al-a">В папке <code class="tag">${esc(d.path)}</code> не найдена база СтройИД.</div><div class="small mut">Возможно, клиент Яндекс Диска ещё не синхронизировал папку на этом компьютере, папку переместили или диск не подключён.</div>`,
    [
      {
        l: "Убрать из списка",
        f: () => {
          A.baseForget(d);
        },
      },
      { l: "Закрыть", c: "pri" },
    ],
  );
};
A.baseForget = (d) => {
  APP.recent = APP.recent.filter((r) => r.path !== d.path);
  saveApp();
  render();
};
A.baseOpenDlg = () =>
  modal(
    "Открыть папку базы",
    `<label class="fld"><span>Папка базы</span><input id="bo-p" value="${esc(DEMO_PATH)}"></label><div class="row mt">${B("Обзор…", "stub", 'data-t="Системный диалог выбора папки"', "sm")}<span class="small mut">Обычно это папка внутри Яндекс Диска</span></div>`,
    [
      { l: "Отмена" },
      {
        l: "Открыть",
        c: "pri",
        f: () => {
          const p = $("#bo-p").value.trim();
          closeModal();
          A.baseOpen({ path: p });
          return false;
        },
      },
    ],
  );
A.baseCreateDlg = () =>
  modal(
    "Новая база",
    `<div style="display:grid;gap:12px"><label class="fld"><span>Название базы</span><input id="bc-n" value="СтройИД — новая база"></label><label class="fld"><span>Папка (будет создана)</span><input id="bc-p" value="C:\\Users\\PTO\\YandexDisk\\СтройИД_новая"></label></div><div class="small mut mt">В папке появятся «_Справочники» с системными шаблонами по РД и пустые «_Корзина», «_Резервные копии». Чтобы коллеги видели базу, откройте им доступ к папке в Яндекс Диске.</div>`,
    [
      { l: "Отмена" },
      {
        l: "Создать",
        c: "pri",
        f: () => {
          const n = $("#bc-n").value.trim() || "СтройИД",
            p = $("#bc-p").value.trim();
          if (!p) {
            toast("Укажите папку");
            return false;
          }
          if (loadBase(p)) {
            toast("В этой папке уже есть база");
            return false;
          }
          const d = seed();
          d.meta.name = n;
          d.projects = [];
          d.lib.orgs = [];
          d.lib.people = [];
          d.lib.orders = [];
          d.lib.base = [];
          d.lib.templates = d.lib.templates.filter((t) => t.locked);
          d.lib.profiles = [
            {
              ...d.lib.profiles[1],
              id: "pf" + uid(),
              family: uid(),
              name: "Базовый профиль",

              date: today(),
              templates: d.lib.templates.map((t) => t.id),
              reqDocs: ["Реестр", "АОСР"],
            },
          ];
          Object.keys(d.lib.signMatrix).forEach(
            (k) => (d.lib.signMatrix[k] = []),
          );
          d.history = [];
          d.locks = {};
          d.builds = [];
          d.trash = [];
          d.ui.exp = {};
          d.ui.sel = {};
          try {
            localStorage.setItem(LSP + p, JSON.stringify(d));
          } catch (e) {}
          closeModal();
          A.baseOpen({ path: p });
          return false;
        },
      },
    ],
  );
A.baseSwitch = () => {
  closeBase();
  location.hash = "#/home";
  render();
};

/* ---------- импорт ---------- */
const IMP_TYPES = [
  ["scan", "Скан акта (АОСР / АООК)"],
  ["sysScheme", "Исполнительная схема системы"],
  ["actScheme", "Схема к акту"],
  ["test", "Акт испытаний / протокол"],
  ["photo", "Фото к акту"],
  ["quality", "Документ качества (новый материал)"],
  ["skip", "Пропустить"],
];
const IMP_DEMO_FOLDER = [
  "ВК/АОСР-007 Монтаж трубопроводов В2.pdf",
  "ВК/АОСР-008 Монтаж трубопроводов К2.pdf",
  "ВК/Схемы/ИС к АОСР-007.pdf",
  "ВК/Протоколы/Протокол промывки В2 к АОСР-008.pdf",
  "ВК/Фото/АОСР-007 фото 1.jpg",
  "ОВ/АОСР-006 Монтаж воздуховодов В2.pdf",
  "ОВ/Сертификаты/Сертификат Воздуховод гибкий Ø160.pdf",
  "АПС/ИС_АПС_общая.pdf",
  "Разное/IMG_2041.jpg",
];
const IMP_DEMO_XLS = [
  [
    "№ п/п",
    "Номер акта",
    "Дата акта",
    "Наименование работ",
    "Место выполнения",
    "Шифр РД",
    "Система",
  ],
  [
    "1",
    "АОСР-007",
    "12.05.2026",
    "Монтаж трубопроводов В2",
    "Подвал, оси 1–6",
    "2026-012-ВК, л. 8",
    "ВК",
  ],
  [
    "2",
    "АОСР-008",
    "15.05.2026",
    "Монтаж трубопроводов К2",
    "Подвал, оси 1–6",
    "2026-012-ВК, л. 9",
    "ВК",
  ],
  [
    "3",
    "АОСР-003",
    "18.05.2026",
    "Прокладка трубопроводов ГВС",
    "Подвал",
    "2026-012-ВК, л. 5",
    "ВК",
  ],
  [
    "4",
    "АОСР-006",
    "20.05.2026",
    "Монтаж воздуховодов системы В2",
    "Технический этаж",
    "2026-012-ОВ, л. 5",
    "ОВ",
  ],
  [
    "5",
    "АОСР-001",
    "02.07.2026",
    "Монтаж трубопроводов обвязки",
    "Котельная",
    "—",
    "ТМ",
  ],
];
const IMP_DEMO_PASS = [
  "Сертификат_Труба_ПНД_SDR17_110.pdf",
  "Паспорт_Насос_Grundfos_CR10.pdf",
  "Декларация_Кабель_ВВГнг(А)-LS_3x2,5.pdf",
  "Сертификат_Радиатор_биметаллический_500-100.pdf",
];
const IMPF = [
  ["num", "Номер акта", 1, /номер акта|№ акта|акт №|^номер$/i],
  ["date", "Дата акта", 0, /дата акта|^дата$/i],
  ["works", "Наименование работ", 1, /наименование работ|^работы$|вид работ/i],
  ["place", "Место выполнения", 0, /место/i],
  ["rd", "Шифр РД", 0, /рд|шифр|чертеж/i],
  ["start", "Начало работ", 0, /начал/i],
  ["end", "Окончание работ", 0, /оконч/i],
  ["sys", "Система (код)", 0, /систем/i],
];
function imp() {
  return (S.ui.imp = S.ui.imp || {
    src: "",
    step: 1,
    pid: S.projects[0]?.id || "",
    sid: "",
    path: "",
    rows: [],
    cols: [],
    map: {},
    res: null,
  });
}
const actNum = (s) => {
  const m = String(s).match(/(АОСР|АООК)[-_ ]?(\d+)/i);
  return m ? m[1].toUpperCase() + "-" + pad(+m[2]) : "";
};
function recog(path, p) {
  const parts = path.split("/");
  const file = parts[parts.length - 1];
  const base = file.replace(/\.[^.]+$/, "");
  const s = p.systems.find(
    (x) => x.code.toLowerCase() === parts[0].toLowerCase(),
  );
  const num = actNum(base);
  const r = {
    file: path,
    on: true,
    sid: s?.id || "",
    num,
    type: "skip",
    name: "",
  };
  if (/\.(jpe?g|png)$/i.test(file)) r.type = num ? "photo" : "skip";
  else if (/^ИС\s*к\s/i.test(base)) r.type = "actScheme";
  else if (/протокол|испытан/i.test(base)) r.type = "test";
  else if (/^(АОСР|АООК)/i.test(base)) {
    r.type = "scan";
    r.name = base.replace(/^(АОСР|АООК)[-_ ]?\d+\s*/i, "");
  } else if (/^ИС[_ ]/i.test(base)) r.type = "sysScheme";
  else if (/сертификат|паспорт|декларац/i.test(base)) {
    r.type = "quality";
    r.name = base.replace(/^(Сертификат|Паспорт|Декларация)\s*/i, "");
  }
  if (r.type === "skip") r.on = false;
  r.name = r.name || base;
  return r;
}
function recogPass(file) {
  const base = file.replace(/\.[^.]+$/, "");
  const t = /^паспорт/i.test(base)
    ? "Паспорт"
    : /^декларац/i.test(base)
      ? "Декларация о соответствии"
      : "Сертификат соответствия";
  const name = base
    .replace(/^(Сертификат|Паспорт|Декларация)_?/i, "")
    .replace(/_/g, " ")
    .replace(/-/g, "/")
    .trim();
  const sim = S.lib.base.find((b) => similar(b.name, name));
  return {
    file,
    on: true,
    name,
    type: t,
    num: "",
    target: sim ? sim.id : "new",
  };
}
const pDate = (v) => {
  v = String(v || "").trim();
  let m = v.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
  if (m)
    return m[3] + "-" + m[2].padStart(2, "0") + "-" + m[1].padStart(2, "0");
  if (/^\d{5}(\.\d+)?$/.test(v))
    return new Date(Date.UTC(1899, 11, 30) + Math.floor(+v) * 864e5)
      .toISOString()
      .slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
  return "";
};
function parseCSV(t) {
  t = t.replace(/^\ufeff/, "");
  const h = t.split("\n")[0];
  const dl =
    (h.match(/;/g) || []).length >= (h.match(/,/g) || []).length
      ? ";"
      : h.includes("\t")
        ? "\t"
        : ",";
  const rows = [];
  let row = [],
    cur = "",
    q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (q) {
      if (c === '"') {
        if (t[i + 1] === '"') {
          cur += '"';
          i++;
        } else q = false;
      } else cur += c;
    } else if (c === '"') q = true;
    else if (c === dl) {
      row.push(cur);
      cur = "";
    } else if (c === "\n") {
      row.push(cur.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cur = "";
    } else cur += c;
  }
  if (cur || row.length) {
    row.push(cur);
    rows.push(row);
  }
  return rows.filter((r) => r.some((x) => String(x).trim()));
}
const unx = (s) =>
  s
    .replace(/&#(\d+);/g, (m, n) => String.fromCodePoint(+n))
    .replace(/&#x([0-9a-f]+);/gi, (m, n) =>
      String.fromCodePoint(parseInt(n, 16)),
    )
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, "&");
async function xlsxRows(file) {
  const z = await zipRead(
    file,
    /^xl\/(sharedStrings\.xml|worksheets\/sheet1\.xml)$/,
  );
  const ss = [
    ...(z["xl/sharedStrings.xml"] || "").matchAll(/<si>([\s\S]*?)<\/si>/g),
  ].map((m) =>
    unx(
      [...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join(""),
    ),
  );
  const out = [];
  [
    ...(z["xl/worksheets/sheet1.xml"] || "").matchAll(
      /<row[^>]*>([\s\S]*?)<\/row>/g,
    ),
  ].forEach((m) => {
    const row = [];
    [...m[1].matchAll(/<c ([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)].forEach((c) => {
      const ref = (c[1].match(/r="([A-Z]+)/) || [])[1] || "A";
      const t = (c[1].match(/t="(\w+)"/) || [])[1];
      let v = ((c[2] || "").match(/<v>([\s\S]*?)<\/v>/) || [])[1];
      if (t === "s") v = ss[+v];
      else if (t === "inlineStr")
        v = unx(((c[2] || "").match(/<t[^>]*>([\s\S]*?)<\/t>/) || [])[1] || "");
      else v = unx(v || "");
      let ci = 0;
      for (const ch of ref) ci = ci * 26 + ch.charCodeAt(0) - 64;
      row[ci - 1] = v;
    });
    out.push([...row].map((x) => x ?? ""));
  });
  return out.filter((r) => r.some((x) => String(x).trim()));
}
function setTable(I, tab) {
  I.cols = tab[0].map(String);
  I.rows = tab
    .slice(1)
    .map((r) => ({ c: I.cols.map((x, i) => String(r[i] ?? "")) }));
  I.map = {};
  IMPF.forEach(([f, , , re]) => {
    const i = I.cols.findIndex((c) => re.test(c));
    I.map[f] = i >= 0 ? String(i) : "";
  });
}
const blkBy = (k) => (S.locks[k] ? lockInfo(k).blockedBy : null);
function impPlan(I) {
  const p = proj(I.pid);
  const out = [];
  if (!p && I.src !== "pass") return out;
  if (I.src === "folder") {
    const planned = {};
    I.rows.forEach((r) => {
      if (r.on && r.type === "scan" && r.sid && r.num)
        (planned[r.sid] = planned[r.sid] || new Set()).add(r.num);
    });
    I.rows.forEach((r, i) => {
      if (!r.on || r.type === "skip") return;
      const s = p.systems.find((x) => x.id === r.sid);
      const fn = r.file.split("/").pop();
      if (r.type === "quality") {
        const b = blkBy("obj:" + p.id);
        out.push(
          b
            ? {
                ok: 0,
                t: `${fn}: общие данные объекта редактирует ${b.user} — пропуск`,
              }
            : {
                ok: 1,
                t: `Материал «${r.name}»: свой материал объекта с документом ${fn}`,
              },
        );
        return;
      }
      if (!s) {
        out.push({ ok: 0, t: `${fn}: не выбрана система — будет пропущен` });
        return;
      }
      {
        const b = blkBy("sys:" + s.id);
        if (b) {
          out.push({
            ok: 0,
            t: `${fn}: систему ${s.code} сейчас редактирует ${b.user} — пропуск, повторите позже`,
          });
          return;
        }
      }
      if (r.type === "sysScheme") {
        out.push({
          ok: 1,
          t: s.scheme.file
            ? `${s.code}: ${fn} станет текущей схемой системы, прежняя будет заменена`
            : `${s.code}: загружается исполнительная схема системы`,
        });
        return;
      }
      const a = s.acts.find((x) => x.num === r.num);
      const willBe = planned[s.id]?.has(r.num);
      if (r.type === "scan") {
        out.push({
          ok: 1,
          t: a
            ? `${s.code} · ${r.num}: скан приложится к существующему акту`
            : `${s.code} · ${r.num}: создаётся акт «${r.name}» со сканом`,
        });
        return;
      }
      if (!r.num || (!a && !willBe)) {
        out.push({
          ok: 0,
          t: `${fn}: не найден акт ${r.num || "(укажите номер)"} — будет пропущен`,
        });
        return;
      }
      out.push({
        ok: 1,
        t: `${s.code} · ${r.num}: ${r.type === "actScheme" ? "своя схема" : r.type === "test" ? "акт испытаний" : "фото"} — ${fn}`,
      });
    });
  }
  if (I.src === "excel") {
    const g = (f) => (I.map[f] === "" || I.map[f] == null ? null : +I.map[f]);
    if (g("num") == null || g("works") == null) {
      out.push({
        ok: 0,
        t: "Укажите колонки «Номер акта» и «Наименование работ»",
      });
      return out;
    }
    const seen = new Set();
    I.rows.forEach((r) => {
      const num = actNum(r.c[g("num")]) || String(r.c[g("num")]).trim();
      const code = g("sys") != null ? String(r.c[g("sys")]).trim() : "";
      const s = I.sid
        ? p.systems.find((x) => x.id === I.sid)
        : p.systems.find((x) => x.code.toLowerCase() === code.toLowerCase());
      if (!s) {
        out.push({
          ok: 0,
          t: `${num}: система «${code || "—"}» не найдена в объекте — пропуск`,
        });
        return;
      }
      const k = s.id + num;
      {
        const b = blkBy("sys:" + s.id);
        if (b) {
          out.push({
            ok: 0,
            t: `${s.code} · ${num}: систему редактирует ${b.user} — пропуск`,
          });
          return;
        }
      }
      if (s.acts.some((a) => a.num === num) || seen.has(k)) {
        out.push({
          ok: 0,
          t: `${s.code} · ${num}: такой номер уже есть — пропуск`,
        });
        return;
      }
      seen.add(k);
      out.push({
        ok: 1,
        t: `${s.code} · ${num}: ${r.c[g("works")]}`,
        s,
        num,
        r,
      });
    });
  }
  if (I.src === "pass")
    I.rows.forEach((r) => {
      if (!r.on) return;
      const b = S.lib.base.find((x) => x.id === r.target);
      out.push({
        ok: 1,
        t: b
          ? `«${b.name}»: добавится документ ${r.type}`
          : `Новая позиция базы «${r.name}» с документом ${r.type}`,
      });
    });
  return out;
}
V.import = () => {
  const I = imp();
  const p = proj(I.pid);
  const st = ["Источник", "Откуда и куда", "Сопоставление", "Импорт"];
  let body = "";
  if (I.step === 1)
    body = `<div class="sysg">${[
      [
        "folder",
        "Папка с готовой ИД",
        "Сканы подписанных актов, схемы, протоколы, сертификаты, фото — разложенные по папкам систем. Программа распознаёт файлы по именам.",
      ],
      [
        "excel",
        "Реестр Excel / CSV",
        "Список актов: номер, дата, наименование работ, место, шифр РД, система. Создаются карточки актов.",
      ],
      [
        "pass",
        "Паспорта и сертификаты",
        "Папка с PDF документов качества — в общую базу паспортов. Похожие позиции определяются автоматически.",
      ],
    ]
      .map(
        ([k, t, d]) =>
          `<a class="sc" href="#" data-a="impSrc" data-v="${k}"><span class="code" style="font-size:15px">${t}</span><span class="small mut">${d}</span></a>`,
      )
      .join("")}</div>`;
  if (I.step === 2) {
    const objSel = F("Объект, куда импортировать", "ui", "", "imp.pid", I.pid, {
      opts: S.projects.map((x) => [x.id, x.name]),
      rr: 1,
    });
    if (I.src === "folder")
      body = `<div class="card"><div class="g2"><label class="fld"><span>Папка с документами</span><input data-ent="ui" data-id="" data-f="imp.path" value="${esc(I.path || "D:\\Объекты\\ЖК Северный корп.2\\ИД")}"></label>${objSel}</div><div class="row mt">${B("Обзор…", "stub", 'data-t="Системный диалог выбора папки"', "sm")}<span class="small mut">Ожидается разложение по папкам систем (ВК, ОВ…), но программа попробует распознать и без него.</span></div></div><div class="row">${B("Назад", "impBack")}${B("Сканировать папку", "impScan", "", "pri")}</div>`;
    if (I.src === "excel")
      body = `<div class="card"><div class="g2">${objSel}${p ? F("Система", "ui", "", "imp.sid", I.sid, { opts: [["", "По колонке «Система» в файле"], ...sysOpts(p)], rr: 1 }) : ""}</div></div><div class="row">${B("Назад", "impBack")}${B(ic("up") + "Выбрать файл .xlsx / .csv", "impFile", "", "pri")}${B("Взять пример реестра", "impDemo")}</div>`;
    if (I.src === "pass")
      body = `<div class="card"><label class="fld"><span>Папка с паспортами и сертификатами</span><input data-ent="ui" data-id="" data-f="imp.path" value="${esc(I.path || "D:\\Сертификаты 2026")}"></label><div class="row mt">${B("Обзор…", "stub", 'data-t="Системный диалог выбора папки"', "sm")}<span class="small mut">Документы попадут в общую базу паспортов</span></div></div><div class="row">${B("Назад", "impBack")}${B("Сканировать папку", "impScan", "", "pri")}</div>`;
  }
  if (I.step === 3) {
    const plan = impPlan(I);
    const ok = plan.filter((x) => x.ok).length;
    if (I.src === "folder")
      body = `<div class="tw"><table class="tbl"><thead><tr><th style="width:34px"></th><th>Файл</th><th style="width:260px">Что это</th><th style="width:150px">Система</th><th style="width:130px">Акт</th></tr></thead><tbody>${I.rows.map((r, i) => `<tr><td><input type="checkbox" data-ent="ui" data-id="" data-f="imp.rows.${i}.on" data-rr="1" ${r.on ? "checked" : ""}></td><td>${esc(r.file)}<div class="t2">${r.type === "skip" ? "не распознано" : "распознано по имени файла"}</div></td><td>${F("", "ui", "", "imp.rows." + i + ".type", r.type, { opts: IMP_TYPES, rr: 1 })}</td><td>${r.type === "quality" ? '<span class="t2">объект</span>' : F("", "ui", "", "imp.rows." + i + ".sid", r.sid, { opts: [["", "— выберите —"], ...p.systems.map((s) => [s.id, s.code])], rr: 1 })}</td><td>${["scan", "actScheme", "test", "photo"].includes(r.type) ? `<input value="${esc(r.num)}" data-ent="ui" data-id="" data-f="imp.rows.${i}.num" data-rr="1" placeholder="АОСР-001">` : ""}</td></tr>`).join("")}</tbody></table></div>`;
    if (I.src === "excel")
      body = `<div class="card"><h3>Какая колонка чему соответствует</h3><div class="g4">${IMPF.map(([f, t, req]) => F(t, "ui", "", "imp.map." + f, I.map[f], { opts: [["", "— нет —"], ...I.cols.map((c, i) => [String(i), c])], rr: 1, req })).join("")}</div></div>
   <div class="tw"><table class="tbl"><thead><tr>${I.cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${I.rows
     .slice(0, 8)
     .map(
       (r) =>
         `<tr>${r.c.map((v) => `<td class="small">${esc(v)}</td>`).join("")}</tr>`,
     )
     .join(
       "",
     )}</tbody></table></div>${I.rows.length > 8 ? `<div class="small mut mt">… ещё ${I.rows.length - 8} строк</div>` : ""}`;
    if (I.src === "pass")
      body = `<div class="tw"><table class="tbl"><thead><tr><th style="width:34px"></th><th>Наименование и файл</th><th style="width:220px">Тип</th><th style="width:150px">Номер</th><th style="width:260px">Куда</th></tr></thead><tbody>${I.rows.map((r, i) => `<tr><td><input type="checkbox" data-ent="ui" data-id="" data-f="imp.rows.${i}.on" data-rr="1" ${r.on ? "checked" : ""}></td><td><input value="${esc(r.name)}" data-ent="ui" data-id="" data-f="imp.rows.${i}.name"><div class="t2" style="margin-top:3px">${esc(r.file)}</div></td><td>${F("", "ui", "", "imp.rows." + i + ".type", r.type, { opts: QDOC })}</td><td><input value="${esc(r.num)}" data-ent="ui" data-id="" data-f="imp.rows.${i}.num" placeholder="№ документа"></td><td>${F("", "ui", "", "imp.rows." + i + ".target", r.target, { opts: [["new", "Новая позиция базы"], ...S.lib.base.map((b) => [b.id, "Добавить к: " + cut(b.name, 34)])], rr: 1 })}</td></tr>`).join("")}</tbody></table></div><div class="small mut mt">Похожие позиции базы подобраны по наименованию — проверьте, чтобы не было дублей.</div>`;
    body += `<div class="row mt" style="margin-top:16px">${B("Назад", "impBack")}<span class="grow"></span><span class="small mut">Будет импортировано: ${ok} из ${plan.length}</span>${B("Далее", "impNext", "", "pri")}</div>`;
  }
  if (I.step === 4) {
    if (I.res)
      body = `<div class="alert al-g"><span class="grow">Импорт выполнен. </span></div><div class="card" style="padding:0">${I.res.map((x) => `<div class="msg"><i style="background:#2fa35b"></i><span>${esc(x)}</span></div>`).join("")}</div><div class="row">${p && I.src !== "pass" ? B("Открыть объект", "nav", `data-h="#/p/${p.id}"`, "pri") : B("Открыть базу паспортов", "nav", 'data-h="#/lib/base"', "pri")}${B("Новый импорт", "impReset")}</div>`;
    else {
      const plan = impPlan(I);
      body = `<div class="card" style="padding:0"><h3 style="padding:14px 16px 4px">Что будет сделано</h3>${plan.map((x) => `<div class="msg ${x.ok ? "" : "w"}"><i style="background:${x.ok ? "#2fa35b" : "#e0a100"}"></i><span>${esc(x.t)}</span></div>`).join("") || '<div class="msg">Нечего импортировать</div>'}</div>
   <div class="small mut mb">Файлы будут скопированы в папку базы. </div><div class="row">${B("Назад", "impBack")}${B("Импортировать", "impRun", "", "pri")}</div>`;
    }
  }
  return `<div class="page">${hdr("Импорт", "Перенос уже готовой исполнительной документации в базу")}<div class="steps">${st.map((t, i) => `<span class="vt${I.step === i + 1 ? " on" : ""}" style="min-width:0"><b>${i + 1}. ${t}</b></span>`).join("")}</div>${body}</div>`;
};
A.impSrc = (d) => {
  const I = imp();
  I.src = d.v;
  I.step = 2;
  I.rows = [];
  I.res = null;
  I.path = "";
  save();
  render();
};
A.impBack = () => {
  const I = imp();
  I.res = null;
  I.step = Math.max(1, I.step - 1);
  save();
  render();
};
A.impReset = () => {
  S.ui.imp = null;
  imp();
  save();
  render();
};
A.impNext = () => {
  const I = imp();
  I.step = 4;
  save();
  render();
};
A.impScan = () => {
  const I = imp();
  const p = proj(I.pid);
  if (I.src === "folder") {
    if (!p) {
      toast("Выберите объект");
      return;
    }
    I.rows = IMP_DEMO_FOLDER.map((f) => recog(f, p));
  } else I.rows = IMP_DEMO_PASS.map(recogPass);
  I.step = 3;
  save();
  render();
  toast(`Найдено файлов: ${I.rows.length} (в прототипе — пример)`);
};
A.impDemo = () => {
  const I = imp();
  setTable(I, IMP_DEMO_XLS);
  I.step = 3;
  save();
  render();
};
A.impFile = async () => {
  const [f] = await pickFiles(".csv,.xlsx,.txt");
  if (!f) return;
  const I = imp();
  let tab = [];
  try {
    tab = /\.xlsx$/i.test(f.name)
      ? await xlsxRows(f)
      : parseCSV(await f.text());
  } catch (e) {
    console.warn(e);
  }
  if (tab.length < 2) {
    toast("Не удалось прочитать таблицу — взят пример реестра");
    tab = IMP_DEMO_XLS;
  }
  setTable(I, tab);
  I.step = 3;
  save();
  render();
  toast(`Прочитано строк: ${I.rows.length}`);
};
A.impRun = () => {
  const I = imp();
  const p = proj(I.pid);
  const plan = impPlan(I);
  if (!plan.some((x) => x.ok)) {
    toast("Нечего импортировать");
    return;
  }
  if (I.src === "pass" && !guard("lib")) return;
  const res = [];
  if (I.src === "folder") {
    const order = [
      "scan",
      "sysScheme",
      "quality",
      "actScheme",
      "test",
      "photo",
    ];
    I.rows
      .filter((r) => r.on && r.type !== "skip")
      .sort((a, b) => order.indexOf(a.type) - order.indexOf(b.type))
      .forEach((r) => {
        const fn = r.file.split("/").pop();
        if (r.type === "quality") {
          if (blkBy("obj:" + p.id)) return;
          p.materials.push({
            id: "m" + uid(),
            baseId: "",
            name: r.name,
            category: "",
            brand: "",
            maker: "",
            note: "Импорт",
            docs: [
              {
                id: uid(),
                type: /паспорт/i.test(fn)
                  ? "Паспорт"
                  : /деклар/i.test(fn)
                    ? "Декларация о соответствии"
                    : "Сертификат соответствия",
                num: "",
                date: "",
                file: fn,
                pages: 1,
              },
            ],
          });
          res.push(`Материал «${r.name}» добавлен в объект`);
          return;
        }
        const s = p.systems.find((x) => x.id === r.sid);
        if (!s || blkBy("sys:" + s.id)) return;
        if (r.type === "sysScheme") {
          Object.assign(s.scheme, {
            file: fn,
            pages: 3,
            stamped: false,
            updated: nowStr(),
            updatedBy: APP.user,
          });
          res.push(`${s.code}: загружена исполнительная схема системы`);
          return;
        }
        let a = s.acts.find((x) => x.num === r.num);
        if (r.type === "scan") {
          if (!a) {
            a = newActObj(s);
            a.num = r.num;
            a.type = r.num.startsWith("АООК") ? "АООК" : "АОСР";
            a.works = r.name;
            s.acts.push(a);
            res.push(`${s.code} · ${r.num}: создан акт «${r.name}»`);
          }
          a.scan = { file: fn, pages: 2 };
          res.push(`${s.code} · ${r.num}: приложен скан`);
          return;
        }
        if (!a) return;
        if (r.type === "actScheme") {
          a.schemes.push({
            ...ROWT.scheme(a),
            name: fn.replace(/\.pdf$/i, ""),
            file: fn,
            pages: 1,
          });
          res.push(`${s.code} · ${r.num}: добавлена схема`);
        }
        if (r.type === "test") {
          a.tests.push({
            ...ROWT.test(a),
            name: fn.replace(/\.pdf$/i, ""),
            file: fn,
            pages: 1,
          });
          res.push(`${s.code} · ${r.num}: добавлен протокол`);
        }
        if (r.type === "photo") {
          a.photos.push({
            id: uid(),
            cap: `Фото ${a.photos.length + 1}. ${a.works}. ${a.place}`,
            img: "",
          });
          res.push(`${s.code} · ${r.num}: добавлено фото`);
        }
      });
  }
  if (I.src === "excel") {
    const g = (f) => (I.map[f] === "" || I.map[f] == null ? null : +I.map[f]);
    plan
      .filter((x) => x.ok)
      .forEach(({ s, num, r }) => {
        const a = newActObj(s);
        a.num = num;
        a.type = num.startsWith("АООК") ? "АООК" : "АОСР";
        a.works = r.c[g("works")] || "";
        if (g("place") != null) a.place = r.c[g("place")];
        if (g("rd") != null) a.rd = r.c[g("rd")];
        ["date", "start", "end"].forEach((f) => {
          if (g(f) != null && pDate(r.c[g(f)])) a[f] = pDate(r.c[g(f)]);
        });
        if (g("date") != null && g("end") == null && a.date)
          a.end = a.start = a.date;
        s.acts.push(a);
        res.push(`${s.code} · ${num}: создан акт «${a.works}»`);
      });
  }
  if (I.src === "pass")
    I.rows
      .filter((r) => r.on)
      .forEach((r) => {
        const doc = {
          id: uid(),
          type: r.type,
          num: r.num,
          date: "",
          file: r.file,
          pages: 1,
        };
        const b = S.lib.base.find((x) => x.id === r.target);
        if (b) {
          b.docs.push(doc);
          res.push(`«${b.name}»: добавлен документ ${r.type}`);
        } else {
          S.lib.base.push({
            id: "b" + uid(),
            name: r.name,
            category: "",
            brand: "",
            maker: "",
            docs: [doc],
          });
          res.push(`В базу паспортов добавлено: «${r.name}»`);
        }
      });
  I.res = res;
  logH(
    `Импорт: ${res.length} операций${p && I.src !== "pass" ? " (" + p.name + ")" : ""}`,
  );
  save();
  render();
  toast(
    "Импорт карточек выполнен. Демонстрационные источники не содержат реальные файлы.",
  );
};
