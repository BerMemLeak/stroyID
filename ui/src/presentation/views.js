/* ===================== ВИДЫ ===================== */
/* ---- Главная: объекты ---- */
V.home = () => {
  return `<div class="page">${hdr("Объекты", `База «${esc(S.meta.name)}» · ${esc(APP.current)}`, B(ic("imp") + "Импорт", "nav", 'data-h="#/import"') + B(ic("plus") + "Новый объект", "newProject", "", "pri"))}
 <div class="objg">${S.projects
   .map((p) => {
     const acts = p.systems.flatMap((s) => s.acts);
     const done = acts.filter((a) => a.status === "Готово").length;
     const pc = acts.length ? Math.round((done / acts.length) * 100) : 0;
     const C = check(p);
     return `<a class="sc" href="#/p/${p.id}"><div class="row"><span class="code">${esc(p.name)}</span><span class="grow"></span>${C.E.length ? `<span class="pill p-r">${C.E.length} ошиб.</span>` : ""}${C.W.length ? `<span class="pill p-a">${C.W.length} предупр.</span>` : ""}</div>
  <div class="nm">${esc(p.address || "Адрес не указан")} · шифр ${esc(p.cipher || "—")}</div>
  <div class="row">${
    sortedSys(p)
      .map((s) => `<span class="pill p-n">${esc(s.code)}</span>`)
      .join("") || '<span class="mut small">Систем пока нет</span>'
  }</div>
  <div><div class="row small mut mb" style="margin-bottom:6px"><span>${acts.length} актов</span><span class="grow"></span><span>готово ${pc}%</span></div><div class="prog"><i style="width:${pc}%"></i></div></div></a>`;
   })
   .join("")}
 <a class="sc new" href="#" data-a="newProject">${ic("plus")}<span>Новый объект</span></a></div>
 <div class="card mt" style="margin-top:22px"><h3>Последние действия</h3>${S.history
   .slice(0, 6)
   .map(
     (h) =>
       `<div class="row small" style="padding:4px 0"><span class="mut" style="width:130px">${esc(h.ts)}</span><span style="width:140px">${esc(h.user)}</span><span>${esc(h.text)}</span></div>`,
   )
   .join("")}</div></div>`;
};

/* ---- Объект ---- */
V.p = (r) => {
  const p = proj(r[1]);
  if (!p) return V.home();
  const tab = r[2] || "overview";
  const C = check(p);
  const base = "#/p/" + p.id;
  const acts = p.systems.flatMap((s) => s.acts);
  const done = acts.filter((a) => a.status === "Готово").length;
  let body = "";
  if (tab === "overview") {
    body = `<div class="kpis"><div class="kpi"><div class="v">${p.systems.length}</div><div class="l">систем</div></div><div class="kpi"><div class="v">${acts.length}</div><div class="l">актов (АОСР/АООК)</div></div><div class="kpi"><div class="v">${acts.length ? Math.round((done / acts.length) * 100) : 0}%</div><div class="l">готово (${done} из ${acts.length})</div></div>
   <a class="kpi" href="${base}/check" style="color:inherit;text-decoration:none"><div class="v" style="color:${C.E.length ? "var(--red)" : C.W.length ? "var(--amb)" : "var(--grn)"}">${C.E.length || C.W.length || "✓"}</div><div class="l">${C.E.length ? "критических ошибок" : C.W.length ? "предупреждений" : "комплект в порядке"}</div></a></div>
  <div class="sysg">${sortedSys(p)
    .map((s) => {
      const d = s.acts.filter((a) => a.status === "Готово").length;
      const pc = s.acts.length ? Math.round((d / s.acts.length) * 100) : 0;
      return `<a class="sc" href="#/s/${s.id}"><div class="row"><span class="code">${esc(s.code)}</span><span class="grow"></span>${s.scheme.file ? '<span class="pill p-g">Схема загружена</span>' : '<span class="small mut">Без схем</span>'}</div><div class="nm">${esc(s.name)}</div>
    <div class="row small">${s.subprofiles.map((sp) => `<span class="pill p-b">${esc(sp.name)}</span>`).join("")}</div>
    <div><div class="row small mut" style="margin-bottom:6px"><span>${s.acts.length} актов · ${s.aik.length} АИК</span><span class="grow"></span><span>${pc}%</span></div><div class="prog"><i style="width:${pc}%"></i></div></div></a>`;
    })
    .join("")}
   <a class="sc new" href="#" data-a="newSystem" data-p="${p.id}">${ic("plus")}<span>Добавить систему</span></a></div>`;
  }
  if (tab === "info") {
    const L = "orgList";
    body = `<datalist id="${L}">${S.lib.orgs.map((o) => `<option value="${esc(o.short)}">`).join("")}</datalist>
  <div class="card"><h3>Основные сведения</h3><div class="g2">${F("Полное наименование объекта", "proj", p.id, "name", p.name, { req: 1, span: 1, rows: 2 })}${F("Общий шифр / номер проекта", "proj", p.id, "cipher", p.cipher, { req: 1 })}${F("Адрес объекта", "proj", p.id, "address", p.address, { req: 1, span: 1 })}</div></div>
  <div class="card"><h3>Участники строительства</h3><div class="g2">${F("Генеральный подрядчик / лицо, осуществляющее строительство", "proj", p.id, "genContractor", p.genContractor, { req: 1, list: L })}${F("Застройщик", "proj", p.id, "developer", p.developer, { list: L })}${F("Технический заказчик", "proj", p.id, "techCustomer", p.techCustomer, { list: L })}${F("Проектная организация", "proj", p.id, "designOrg", p.designOrg, { list: L })}${F("Авторский надзор", "proj", p.id, "supervision", p.supervision, { list: L })}${F("Эксплуатирующая организация", "proj", p.id, "operator", p.operator, { list: L })}</div></div>
  <div class="card"><h3>Договор и реквизиты</h3><div class="g3">${F("Номер договора / контракта", "proj", p.id, "contract", p.contract)}${F("Дата начала строительства", "proj", p.id, "startDate", p.startDate, { type: "date" })}<div class="fld"><span>Логотип для титульных листов</span><div class="row">${p.logo ? `<img src="${p.logo}" style="height:34px;border-radius:4px">` : ""}${B(p.logo ? "Заменить" : "Загрузить PNG/JPG", "logoPick", `data-ent="proj" data-id="${p.id}"`, "sm")}</div></div></div>
   <div class="mt">${p.extra.map((x) => `<div class="row mb"><input style="max-width:300px" value="${esc(x.k)}" data-ent="proj" data-id="${p.id}" data-f="extra.#${x.id}.k"><input class="grow" style="width:auto" value="${esc(x.v)}" data-ent="proj" data-id="${p.id}" data-f="extra.#${x.id}.v"><code class="tag">{{${esc(slug(x.k))}}}</code>${B(ic("trash"), "extraRm", `data-p="${p.id}" data-x="${x.id}"`, "sm icon ghost")}</div>`).join("")}${B("+ Дополнительный реквизит", "extraAdd", `data-p="${p.id}"`, "sm ghost")}</div></div>
  <div class="row">${B("Удалить объект", "del", `data-ent="proj" data-id="${p.id}"`, "dng")}</div>`;
  }
  if (tab === "mats") body = matsTab(p);
  if (tab === "ozhr") {
    body =
      `<div class="row mb"><span class="mut small grow">Журналы объекта. Специальные журналы систем ведутся внутри системы.</span>${B("+ Журнал объекта", "newJournal", `data-p="${p.id}"`, "pri")}</div>` +
      journalList(p.journals);
  }
  if (tab === "check") body = checkView(C);
  if (tab === "files") body = explorer([objDir(p)]);
  return `<div class="page">${hdr(esc(p.name), esc(p.address) + (p.cipher ? " · шифр " + esc(p.cipher) : ""), B(ic("plus") + "Система", "newSystem", `data-p="${p.id}"`) + B(ic("layers") + "Собрать том", "nav", `data-h="#/build/${p.id}"`), '<a href="#/home">Объекты</a>')}
 ${tabs(base, tab, [
   ["overview", "Обзор"],
   ["info", "Сведения об объекте"],
   ["mats", "Материалы и паспорта", p.materials.length],
   ["ozhr", "Журнал работ", p.journals.length],
   ["check", "Проверка", C.E.length || C.W.length, C.E.length],
   ["files", "Файлы"],
 ])}${body}</div>`;
};
function checkView(C) {
  const it = (x, c) =>
    `<div class="msg ${c}" data-a="nav" data-h="${x.l}"><i></i><span>${esc(x.t)}</span></div>`;
  return `${C.E.length ? `<div class="alert al-r"><b>Сборка тома будет заблокирована:</b> критических ошибок — ${C.E.length}.</div>` : C.W.length ? `<div class="alert al-a">Критических ошибок нет, можно собирать. Предупреждений — ${C.W.length}.</div>` : '<div class="alert al-g">Комплект готов к сборке.</div>'}
 ${C.E.length ? `<div class="card" style="padding:0"><h3 style="padding:14px 16px 0;color:var(--red)">Критические ошибки</h3>${C.E.map((x) => it(x, "e")).join("")}</div>` : ""}
 ${C.W.length ? `<div class="card" style="padding:0"><h3 style="padding:14px 16px 0;color:var(--amb)">Предупреждения</h3>${C.W.map((x) => it(x, "w")).join("")}</div>` : ""}`;
}
function matsTab(p) {
  const q = S.ui.f["mq" + p.id] || "";
  const L = p.materials.filter(
    (m) =>
      !q ||
      norm(
        mName(m) +
          " " +
          mF(m, "maker") +
          " " +
          mDocs(m)
            .map((d) => d.num)
            .join(" "),
      ).includes(norm(q)),
  );
  return `<div class="row mb">${F("", "ui", "", "f.mq" + p.id, q, { rr: 1, ph: "Найти материал или № документа", style: "width:320px" })}<span class="grow"></span>${B(ic("link") + "Из базы паспортов", "matFromBase", `data-p="${p.id}"`)}${B(ic("plus") + "Свой материал", "newMat", `data-p="${p.id}"`, "pri")}</div>
 ${
   L.length
     ? `<div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th>Производитель</th><th>Документы качества</th><th>Источник</th><th class="num">В актах</th></tr></thead><tbody>${L.map(
         (m) => {
           const n = p.systems.reduce(
             (c, s) =>
               c + s.acts.filter((a) => a.materials.includes(m.id)).length,
             0,
           );
           const docs = mDocs(m);
           return `<tr class="cl" data-a="nav" data-h="#/m/${m.id}"><td><b style="font-weight:550">${esc(mName(m))}</b><div class="t2">${esc(mF(m, "category"))}</div></td><td class="t2">${esc(mF(m, "maker"))}</td><td>${docs.length ? docs.map((d) => `<span class="pill p-n" style="margin:1px">${esc(d.type)}</span>`).join(" ") : '<span class="pill p-r">нет</span>'}</td><td>${m.baseId ? '<span class="pill p-b">' + ic("link", "ic") + " База</span>" : '<span class="pill p-n">Свой</span>'}</td><td class="num">${n}</td></tr>`;
         },
       ).join("")}</tbody></table></div>`
     : '<div class="empty">Материалов нет. Добавьте из базы паспортов или создайте свой.</div>'
 }
 <div class="small mut mt">Материалы из базы связаны с ней: обновление паспорта в базе применяется во всех объектах. Количество и поставки не учитываются.</div>`;
}
function journalList(list) {
  return list.length
    ? `<div class="tw"><table class="tbl"><thead><tr><th>Журнал</th><th>Вид</th><th>Ведение</th><th class="num">Записей / листов</th></tr></thead><tbody>${list.map((j) => `<tr class="cl" data-a="nav" data-h="#/j/${j.id}"><td><b style="font-weight:550">${esc(j.name)}</b></td><td class="t2">${esc(j.kind)}</td><td>${j.mode === "A" ? '<span class="pill p-b">Ввод записей</span>' : '<span class="pill p-n">Готовый PDF</span>'}</td><td class="num">${j.mode === "A" ? j.rows.length + " зап." : (j.pages || 0) + " л."}</td></tr>`).join("")}</tbody></table></div>`
    : '<div class="empty">Журналов нет</div>';
}

/* ---- Система ---- */
V.s = (r) => {
  const c = ctx("sys", r[1]);
  const s = c.o,
    p = c.p;
  if (!s) return V.home();
  const tab = r[2] || "acts";
  const base = "#/s/" + s.id;
  let body = "";
  if (tab === "acts") {
    const L = sortActs(s.acts);
    const sel = S.ui.sel;
    const ns = L.filter((a) => sel[a.id]).length;
    body = `  <div class="row mb"><span class="mut small grow">${L.length} актов · готово ${L.filter((a) => a.status === "Готово").length}</span>${B(ic("plus") + "Новый АОСР", "newAct", `data-s="${s.id}"`, "pri")}</div>
  ${
    L.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th style="width:34px"><input type="checkbox" data-a="selAll" data-s="${s.id}" ${ns && ns === L.length ? "checked" : ""}></th><th>Номер</th><th>Работы</th><th>Комплекты</th><th class="num">Схемы</th><th class="num">Фото</th><th>Дата</th><th>Статус</th></tr></thead><tbody>
  ${L.map((a) => `<tr class="cl${sel[a.id] ? " sel" : ""}" data-a="nav" data-h="#/a/${a.id}"><td data-a="selOne" data-id="${a.id}"><input type="checkbox" ${sel[a.id] ? "checked" : ""} tabindex="-1" style="pointer-events:none"></td><td><b style="font-weight:600">${esc(a.num)}</b></td><td>${esc(a.works)}<div class="t2">${esc(a.place)}</div></td><td>${a.subs.map((id) => `<span class="pill p-b" style="margin:1px">${esc((spOf(s, id)?.name || "").replace(s.code + " — ", ""))}</span>`).join("") || '<span class="pill p-r">нет</span>'}</td><td class="num">${a.schemes.length ? a.schemes.length : '<span class="mut">—</span>'}</td><td class="num">${a.photos.length || '<span class="mut">—</span>'}</td><td class="t2">${fmtD(a.date)}</td><td>${stP(a.status)}</td></tr>`).join("")}</tbody></table></div>`
      : '<div class="empty">АОСР ещё нет. Нажмите «Новый АОСР».</div>'
  }
  ${ns ? `<div class="selbar"><span class="grow">Выбрано: <b>${ns}</b></span>${B("Отметить «Готово»", "massStatus", 'data-v="Готово"', "sm")}${B("«В работе»", "massStatus", 'data-v="В работе"', "sm")}${B("Дублировать", "massDup", "", "sm")}${B("Удалить", "massDel", "", "sm")}${B("×", "selClear", 'title="Снять выделение"', "sm icon")}</div>` : ""}`;
  }
  if (tab === "scheme") body = schemeTab(p, s);
  if (tab === "aik") {
    body = `<div class="row mb"><span class="mut small grow">Акт входного контроля создаётся на материал объекта и подтягивает его документы качества.</span>${B(ic("plus") + "Новый АИК", "newAik", `data-s="${s.id}"`, "pri")}</div>
  ${
    s.aik.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Номер</th><th>Материал</th><th>Документы</th><th>Привязан к актам</th><th>Дата</th><th>Статус</th></tr></thead><tbody>${s.aik
          .map((k) => {
            const m = pMat(p, k.materialId);
            const used = s.acts.filter((a) =>
              Object.values(a.aikLinks).includes(k.id),
            );
            return `<tr class="cl" data-a="nav" data-h="#/k/${k.id}"><td><b style="font-weight:600">${esc(k.num)}</b></td><td>${m ? esc(mName(m)) : '<span class="pill p-r">удалён</span>'}</td><td class="num">${m ? mDocs(m).length : "—"}</td><td class="t2">${used.map((a) => esc(a.num)).join(", ") || "—"}</td><td class="t2">${fmtD(k.date)}</td><td>${stP(k.status)}</td></tr>`;
          })
          .join("")}</tbody></table></div>`
      : '<div class="empty">АИК нет</div>'
  }`;
  }
  if (tab === "jr")
    body =
      `<div class="row mb"><span class="mut small grow">Специальные журналы системы: сварочных, бетонных, антикоррозийных, монтажных работ или свой.</span>${B(ic("plus") + "Журнал", "newJournal", `data-s="${s.id}"`, "pri")}</div>` +
      journalList(s.journals);
  if (tab === "subs") body = subsTab(p, s);
  if (tab === "files") body = explorer([objDir(p), sysDir(s)]);
  if (tab === "params")
    body = `<div class="card"><h3>Параметры системы</h3><div class="g4">${F("Код (имя папки системы)", "sys", s.id, "code", s.code, { req: 1, rr: 1, attrs: ` data-orig="${esc(sysDir(s))}" data-fsk="sys"` })}${F("Наименование", "sys", s.id, "name", s.name, { req: 1, rr: 1, style: "grid-column:span 2" })}${F("Порядок в объекте и томе", "sys", s.id, "order", s.order, { type: "number", rr: 1 })}${F("Шифр рабочей документации", "sys", s.id, "cipher", s.cipher, { style: "grid-column:span 2" })}</div></div><div class="row">${B("Удалить систему", "del", `data-ent="sys" data-id="${s.id}"`, "dng")}</div>`;
  return `<div class="page">${hdr(`${esc(s.code)} <span class="mut" style="font-weight:500">${esc(s.name)}</span>`, `${s.scheme.file ? '<span class="pill p-g">Схема системы загружена</span>' : '<span class="small mut">Без схем</span>'} ${s.subprofiles.map((sp) => `<span class="pill p-b">${esc(sp.name)}</span>`).join(" ")}`, B(ic("plus") + "Новый АОСР", "newAct", `data-s="${s.id}"`), `<a href="#/p/${p.id}">${esc(p.name)}</a>`)}
 ${tabs(base, tab, [
   ["acts", "АОСР", s.acts.length],
   ["scheme", "Исполнительная схема", s.scheme.file ? "" : "!", !s.scheme.file],
   ["aik", "АИК", s.aik.length],
   ["jr", "Журналы", s.journals.length],
   ["subs", "Подпрофили", s.subprofiles.length],
   ["files", "Файлы"],
   ["params", "Параметры"],
 ])}${body}</div>`;
};

/* ---- Исполнительная схема системы ---- */
const cut = (s, n) => {
  s = String(s || "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
};
function stampRect(sc, w, h) {
  const sw = 120,
    sh = 46;
  const p = sc.pos;
  let x, y;
  if (p === "Правый верхний угол") {
    x = w - 5 - sw - 3;
    y = 8;
  } else if (p === "Левый верхний угол") {
    x = 23;
    y = 8;
  } else if (p === "Над основной надписью") {
    x = w - 5 - 185;
    y = h - 5 - 55 - sh - 4;
  } else if (p === "Левый нижний угол") {
    x = 23;
    y = h - 5 - sh - 3;
  } else {
    x = 20 + ((w - 25 - sw) * (+sc.mx || 0)) / 100;
    y = 5 + ((h - 10 - sh) * (+sc.my || 0)) / 100;
  }
  return { x, y, sw, sh };
}
function sheetSvg(sc, o) {
  const fmt = sc.format === "авто" ? "A3" : sc.format;
  let [w, h] = {
    A4: [210, 297],
    A3: [297, 420],
    A2: [420, 594],
    A1: [594, 841],
  }[fmt] || [297, 420];
  if (sc.orient === "Альбомная") [w, h] = [h, w];
  const ex = person(o.execId);
  const R = stampRect(sc, w, h);
  const tb = { x: w - 5 - 185, y: h - 5 - 55, w: 185, h: 55 };
  const ov = !(
    R.x + R.sw < tb.x ||
    R.x > tb.x + tb.w ||
    R.y + R.sh < tb.y ||
    R.y > tb.y + tb.h
  );
  let g = "";
  for (let i = 0; i < 6; i++) {
    const xx = 30 + (i * (w - 60)) / 5;
    g += `<line x1="${xx}" y1="20" x2="${xx}" y2="${h - 70}" stroke="#bbb" stroke-dasharray="6 2 1 2" stroke-width=".4"/><circle cx="${xx}" cy="16" r="4" fill="none" stroke="#999" stroke-width=".4"/><text x="${xx}" y="17.5" font-size="4" text-anchor="middle" fill="#777">${i + 1}</text>`;
  }
  g += `<polyline points="40,${h * 0.55} ${w * 0.35},${h * 0.55} ${w * 0.35},${h * 0.3} ${w * 0.7},${h * 0.3}" fill="none" stroke="#1a5fb4" stroke-width="1.4"/><polyline points="40,${h * 0.62} ${w * 0.45},${h * 0.62} ${w * 0.45},${h * 0.4} ${w * 0.75},${h * 0.4}" fill="none" stroke="#c0392b" stroke-width="1.4"/>`;
  const st = `<g><rect x="${R.x}" y="${R.y}" width="${R.sw}" height="${R.sh}" fill="#fff" stroke="${ov ? "#d00" : "#0b3d91"}" stroke-width="${ov ? 1.2 : 0.6}"/>
  <text x="${R.x + R.sw / 2}" y="${R.y + 7}" font-size="4.6" font-weight="bold" text-anchor="middle" fill="#0b3d91">ИСПОЛНЕНО ПО РАБОЧИМ ДОКУМЕНТАМ</text>
  <text x="${R.x + 3}" y="${R.y + 14}" font-size="3.6" fill="#0b3d91">шифр: ${esc(cut(sc.rd, 52))}</text>
  <text x="${R.x + 3}" y="${R.y + 20}" font-size="3.6" fill="#0b3d91">Отклонения: ${esc(cut(sc.tol, 48))}</text>
  <text x="${R.x + 3}" y="${R.y + 26}" font-size="3.6" fill="#0b3d91">${esc(cut(org(ex?.orgId)?.short || "", 40))}</text>
  <text x="${R.x + 3}" y="${R.y + 32}" font-size="3.6" fill="#0b3d91">${esc(cut(ex?.position || "Исполнитель не выбран", 40))}</text>
  <text x="${R.x + 3}" y="${R.y + 40}" font-size="3.6" fill="#0b3d91">${esc(ex?.fioShort || "")}   ________   ${fmtD(o.date)}</text></g>`;
  return {
    svg: `<svg viewBox="0 0 ${w} ${h}" width="${Math.min(w * 1.6, 640)}" xmlns="http://www.w3.org/2000/svg" font-family="Arial"><rect x="0" y="0" width="${w}" height="${h}" fill="#fff"/><rect x="20" y="5" width="${w - 25}" height="${h - 10}" fill="none" stroke="#000" stroke-width=".7"/>${g}
  <rect x="${tb.x}" y="${tb.y}" width="185" height="55" fill="#fafafa" stroke="#000" stroke-width=".6"/><line x1="${tb.x}" y1="${tb.y + 15}" x2="${tb.x + 185}" y2="${tb.y + 15}" stroke="#000" stroke-width=".3"/><line x1="${tb.x + 65}" y1="${tb.y}" x2="${tb.x + 65}" y2="${tb.y + 55}" stroke="#000" stroke-width=".3"/>
  <text x="${tb.x + 125}" y="${tb.y + 10}" font-size="5" text-anchor="middle">${esc(cut(o.cipher, 30))}</text><text x="${tb.x + 125}" y="${tb.y + 30}" font-size="3.8" text-anchor="middle">${esc(cut(o.name, 50))}</text><text x="${tb.x + 125}" y="${tb.y + 47}" font-size="3.6" text-anchor="middle">Основная надпись (ГОСТ 21.101)</text>${st}</svg>`,
    ov,
  };
}
function schemeTab(p, s) {
  const sc = s.scheme;
  const k = "st" + s.id;
  const spId = spOf(s, S.ui.f[k]) ? S.ui.f[k] : s.subprofiles[0]?.id;
  const sp = spOf(s, spId);
  const lastEnd =
    s.acts
      .map((a) => a.end)
      .filter(Boolean)
      .sort()
      .pop() || today();
  const allowed = S.lib.signMatrix["Исполнительные схемы"] || [];
  const { svg, ov } = sheetSvg(sc, {
    cipher: s.cipher || p.cipher,
    name: "Исполнительная схема системы " + s.code,
    execId: sp?.execId,
    date: lastEnd,
  });
  return `<div class="alert al-b"><span class="grow">Один файл схемы на систему — общий для всех подпрофилей и всех АОСР системы. Штамп «Исполнено» ставится на этот же файл, в разных комплектах отличается только исполнитель в штампе.</span></div>
 <div class="card"><h3>Файл исполнительной схемы<span class="r">${B(ic("up") + (sc.file ? "Заменить PDF" : "Загрузить PDF"), "schemeFile", `data-s="${s.id}"`, sc.file ? "sm" : "sm pri")}</span></h3>
 ${fileBox(sc.file, sc.pages, (sc.stamped ? '<span class="pill p-g">Штамп наложен</span>' : "") + (sc.file ? B("Открыть", "fileOpen", `data-path="${esc(winPath([objDir(p), sysDir(s), "Исполнительная схема", sc.file]))}"`, "sm ghost") : ""), sc.updated ? " · обновлён " + esc(sc.updated) + (sc.updatedBy ? ", " + esc(sc.updatedBy) : "") : "")}
 </div>
 <div class="cols"><div class="card"><h3>Штамп «Исполнено»</h3><div class="g2">
  ${F("Шифр РД в штампе", "sys", s.id, "scheme.rd", sc.rd, { span: 1, rr: 1 })}${F("Отклонения", "sys", s.id, "scheme.tol", sc.tol, { span: 1, rr: 1 })}
  ${F("Формат листа", "sys", s.id, "scheme.format", sc.format, { opts: FORMATS, rr: 1 })}${F("Ориентация", "sys", s.id, "scheme.orient", sc.orient, { opts: ORIENT, rr: 1 })}
  ${F("Положение штампа", "sys", s.id, "scheme.pos", sc.pos, { opts: STAMP_POS, rr: 1, span: 1 })}
  ${sc.pos === "Задать вручную" ? F("Смещение по X, %", "sys", s.id, "scheme.mx", sc.mx, { type: "number", rr: 1 }) + F("Смещение по Y, %", "sys", s.id, "scheme.my", sc.my, { type: "number", rr: 1 }) : ""}</div>
  <div class="mt">${CK("Ставить штамп на все листы файла", "sys", s.id, "scheme.allPages", sc.allPages)}</div>
  <div class="small mut" style="margin:18px 0 8px;font-weight:600">Исполнитель в штампе по подпрофилям</div>
  <div style="display:grid;gap:10px">${s.subprofiles.map((x) => F(x.name, "sys", s.id, "subprofiles.#" + x.id + ".execId", x.execId, { opts: peopleOpts("— не выбран —", allowed.concat(x.execId || [])), rr: 1 })).join("")}</div>
  <div class="row mt" style="margin-top:16px">${B(ic("stamp") + "Наложить штамп", "stampApply", `data-s="${s.id}"`, "pri")}</div></div>
 <div class="card"><h3>Предпросмотр листа<span class="r row">${s.subprofiles.length > 1 ? s.subprofiles.map((x) => `<span class="chk${x.id === spId ? " on" : ""}" data-a="setUi" data-k="${k}" data-v="${x.id}">${esc(x.name.replace(s.code + " — ", ""))}</span>`).join("") : ""}</span></h3>
  ${ov ? '<div class="alert al-r">Штамп перекрывает основную надпись — измените положение.</div>' : ""}<div class="sheetwrap">${svg}</div>
  <div class="small mut mt">${sc.file ? "Условный лист: в приложении здесь будет страница загруженного PDF." : "Файл не загружен — показан условный лист."}</div></div></div>`;
}
function subsTab(p, s) {
  const allowed = S.lib.signMatrix["АОСР"] || [];
  return `<div class="alert al-b"><span class="grow">Подпрофиль — отдельный комплект для заказчика: профиль оформления, подписанты по умолчанию и исполнитель в штампе схемы. АОСР вводится один раз, а в его карточке отмечается, в какие комплекты он входит. Каждый подпрофиль — отдельный том 2.х.</span>${B(ic("plus") + "Подпрофиль", "spAdd", `data-s="${s.id}"`, "sm")}</div>
 ${s.subprofiles
   .map((sp) => {
     const n = s.acts.filter((a) => a.subs.includes(sp.id)).length;
     const pf = prof(sp.profileId);
     return `<div class="card"><h3>${esc(sp.name)} <span class="pill p-n">${n} из ${s.acts.length} актов</span><span class="r">${s.subprofiles.length > 1 ? B(ic("trash"), "spRm", `data-s="${s.id}" data-sp="${sp.id}" title="Удалить подпрофиль"`, "sm icon ghost") : ""}</span></h3>
  <div class="g3">${F("Название", "sys", s.id, "subprofiles.#" + sp.id + ".name", sp.name, { rr: 1 })}${F("Профиль заказчика", "sys", s.id, "subprofiles.#" + sp.id + ".profileId", sp.profileId, { opts: S.lib.profiles.map((x) => [x.id, x.name]), rr: 1, hint: pf ? esc(QRULES[pf.quality]) : "" })}${F("Исполнитель в штампе схемы", "sys", s.id, "subprofiles.#" + sp.id + ".execId", sp.execId, { opts: peopleOpts(), rr: 1 })}</div>
  <div class="small mut" style="margin:16px 0 8px;font-weight:600">Подписанты по умолчанию</div>
  <div class="g2">${DOC_ROLES.map((r, i) => F(ROLE_SH[i], "sys", s.id, "subprofiles.#" + sp.id + ".signers.r" + i, sp.signers["r" + i], { opts: peopleOpts("— не выбран —", allowed.concat(sp.signers["r" + i] || [])), rr: 1 })).join("")}</div></div>`;
   })
   .join("")}`;
}

/* ---- АОСР / АООК ---- */
V.a = (r) => {
  const c = ctx("act", r[1]);
  const a = c.o,
    s = c.s,
    p = c.p;
  if (!a) return V.home();
  const tab = r[2] || "main";
  const base = "#/a/" + a.id;
  const req = new Set();
  a.subs.forEach((id) =>
    prof(spOf(s, id)?.profileId)?.reqFields.forEach((f) => req.add(f)),
  );
  const rq = (f) => (req.has(f) ? 1 : 0);
  const dup = s.acts.some((x) => x.id !== a.id && x.num === a.num);
  const allowed = S.lib.signMatrix["АОСР"] || [];
  let body = "";
  if (tab === "main") {
    const ovr = DOC_ROLES.filter((x, i) => a.signers["r" + i]).length;
    const inSubs = s.subprofiles.filter((sp) => a.subs.includes(sp.id));
    body = `<div class="card"><h3>Реквизиты</h3><div class="g4">${F("Тип акта", "act", a.id, "type", a.type, { opts: ["АОСР", "АООК"], rr: 1 })}${F("Номер (имя папки акта)", "act", a.id, "num", a.num, { rr: 1, attrs: ` data-orig="${esc(actDir(a))}" data-fsk="act"`, hint: dup ? `<span style="color:var(--red)">Номер уже есть в системе. Свободный: ${esc(nextNum(s, a.type, a.id))}</span>` : "" })}${F("Дата акта", "act", a.id, "date", a.date, { type: "date", rr: 1 })}${F("Статус", "act", a.id, "status", a.status, { opts: ["В работе", "Готово"], rr: 1 })}
   ${F("Начало работ (п. 5)", "act", a.id, "start", a.start, { type: "date", rr: 1, req: rq("start") })}${F("Окончание работ (п. 5)", "act", a.id, "end", a.end, { type: "date", rr: 1, req: rq("end") })}</div></div>
  <div class="card"><h3>Содержание</h3><div class="g2">${F("Наименование работ (п. 1)", "act", a.id, "works", a.works, { rows: 2, req: rq("works"), span: 1, rr: 1 })}${F("Место выполнения", "act", a.id, "place", a.place, { req: rq("place") })}${F("Рабочая документация (п. 2)", "act", a.id, "rd", a.rd, { req: rq("rd") })}
   ${F("Нормативные документы (п. 6)", "act", a.id, "norms", a.norms, { rows: 2, req: rq("norms") })}${F("Разрешённые последующие работы (п. 7)", "act", a.id, "next", a.next, { rows: 2, req: rq("next") })}</div></div>
  <div class="card"><h3>Входит в комплекты</h3><div class="row">${s.subprofiles
    .map((sp) => {
      const on = a.subs.includes(sp.id);
      return `<span class="chk${on ? " on" : ""}" data-a="subTog" data-id="${a.id}" data-sp="${sp.id}">${on ? ic("check") : ""}${esc(sp.name)}</span>`;
    })
    .join("")}</div>
   <div class="small mut mt">Акт вводится один раз и попадает в том каждого отмеченного подпрофиля. Обязательные поля (<b class="req">*</b>) берутся из профилей отмеченных комплектов.</div></div>
  <details class="card"${ovr ? " open" : ""}><summary>Подписанты <span class="pill ${ovr ? "p-b" : "p-n"}">${ovr ? "заменено: " + ovr : "как в подпрофиле"}</span></summary>
   <div class="tw"><table class="tbl"><thead><tr><th>Роль</th><th>По умолчанию из подпрофиля</th><th style="width:40%">В этом акте</th></tr></thead><tbody>${DOC_ROLES.map(
     (
       x,
       i,
     ) => `<tr><td>${esc(ROLE_SH[i])}</td><td class="t2">${inSubs.map((sp) => esc(person(sp.signers["r" + i])?.fioShort || "не назначен") + (s.subprofiles.length > 1 ? ' <span class="mut">(' + esc(sp.name.replace(s.code + " — ", "")) + ")</span>" : "")).join("<br>") || "—"}</td>
   <td>${F("", "act", a.id, "signers.r" + i, a.signers["r" + i] || "", { opts: [["", "Как в подпрофиле"], ...peopleOpts("", allowed.concat(a.signers["r" + i] || [])).slice(1)], rr: 1 })}</td></tr>`,
   ).join("")}</tbody></table></div>
   <div class="small mut mt">Замена действует только в этом акте — для всех его комплектов.</div></details>
  ${remarksCard("act", a.id, a.remarks)}`;
  }
  if (tab === "mat") {
    body = `<div class="card"><h3>Применённые материалы (п. 3)<span class="r">${B(ic("plus") + "Выбрать из материалов объекта", "actMatAdd", `data-id="${a.id}"`, "sm")}</span></h3>
  ${
    a.materials.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Материал</th><th>Документы качества</th><th style="width:250px">Акт входного контроля</th><th style="width:40px"></th></tr></thead><tbody>${a.materials
          .map((mid) => {
            const m = pMat(p, mid);
            const rm = B(
              ic("trash"),
              "actMatRm",
              `data-id="${a.id}" data-m="${mid}" title="Убрать из акта"`,
              "sm icon ghost",
            );
            if (!m)
              return `<tr><td colspan="3"><span class="pill p-r">Материал удалён из объекта</span></td><td>${rm}</td></tr>`;
            const ks = s.aik.filter((k) => k.materialId === mid);
            return `<tr><td><a href="#/m/${m.id}">${esc(mName(m))}</a>${m.baseId ? ' <span class="pill p-b">База</span>' : ""}</td><td class="t2">${
              mDocs(m)
                .map((d) => esc(d.type + " № " + d.num))
                .join("<br>") || '<span class="pill p-r">нет документов</span>'
            }</td>
   <td>${ks.length ? F("", "act", a.id, "aikLinks." + mid, a.aikLinks[mid] || "", { opts: [["", "— не привязан —"], ...ks.map((k) => [k.id, k.num + " от " + fmtD(k.date)])], rr: 1 }) : B(ic("plus") + "Создать АИК", "aikCreate", `data-id="${a.id}" data-m="${mid}"`, "sm")}</td><td>${rm}</td></tr>`;
          })
          .join("")}</tbody></table></div>`
      : '<div class="empty">Материалы не выбраны</div>'
  }
  <div class="small mut mt">Нужного материала нет? Добавьте его в объект на вкладке <a href="#/p/${p.id}/mats">«Материалы и паспорта»</a> — из базы паспортов или свой.</div></div>`;
  }
  if (tab === "files") body = explorer([objDir(p), sysDir(s), actDir(a)]);
  if (tab === "att") {
    const sc = a.scan || { file: "", pages: 0 };
    body = `<div class="card"><h3>Скан подписанного акта <span class="mut small" style="font-weight:400">необязательно</span><span class="r">${sc.file ? B("Открыть", "fileOpen", `data-path="${esc(winPath([objDir(p), sysDir(s), actDir(a), sc.file]))}"`, "sm ghost") + B(ic("trash"), "scanRm", `data-id="${a.id}" title="Убрать скан"`, "sm icon ghost") : ""}${B(sc.file ? "Заменить" : "Загрузить", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="scan"`, "sm")}</span></h3>${sc.file ? fileBox(sc.file, sc.pages, "", " · в том вшивается скан вместо сформированного акта") : '<div class="small mut">Когда акт подписан, приложите скан — в томе он заменит сформированный документ.</div>'}</div>
  <div class="card"><h3>Исполнительная схема системы <span class="pill p-n">прикладывается автоматически</span><span class="r">${B("Открыть", "nav", `data-h="#/s/${s.id}/scheme"`, "sm ghost")}</span></h3>${fileBox(s.scheme.file, s.scheme.pages, "", " · общая для всех актов " + esc(s.code))}${!s.scheme.file ? '<div class="alert al-a mt" style="margin-bottom:0">Схема системы не загружена. Это предупреждение — сборка тома не блокируется.</div>' : ""}</div>
  <div class="card"><h3>Свои схемы к акту <span class="mut small" style="font-weight:400">необязательно</span><span class="r">${B(ic("plus") + "Схема", "rowAdd", `data-ent="act" data-id="${a.id}" data-p="schemes" data-k="scheme"`, "sm")}</span></h3>
  ${
    a.schemes.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th>Файл</th><th style="width:96px">Формат</th><th style="width:130px"></th></tr></thead><tbody>${a.schemes
          .map(
            (
              x,
              i,
            ) => `<tr><td><input value="${esc(x.name)}" data-ent="act" data-id="${a.id}" data-f="schemes.#${x.id}.name"></td>
   <td><div class="row" style="flex-wrap:nowrap">${x.file ? `<span class="small">${esc(x.file)}</span><span class="t2 small">${x.pages} л.</span>` : '<span class="pill p-r">нет файла</span>'}${B(x.file ? "Заменить" : "Загрузить", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="schemes.#${x.id}"`, "sm ghost")}</div></td>
   <td>${F("", "act", a.id, "schemes.#" + x.id + ".format", x.format, { opts: FORMATS, rr: 1 })}</td><td><div class="row" style="flex-wrap:nowrap;gap:4px">${B(ic("stamp"), "ownPrev", `data-id="${a.id}" data-x="${x.id}" title="Штамп и предпросмотр"`, "sm icon ghost")}${mvB("act", a.id, "schemes", i)}${B(ic("trash"), "rowRm", `data-ent="act" data-id="${a.id}" data-p="schemes" data-r="${x.id}" title="Удалить"`, "sm icon ghost")}</div></td></tr>`,
          )
          .join("")}</tbody></table></div>`
      : '<div class="small mut">Своих схем нет — к акту приложена только схема системы.</div>'
  }</div>
  <div class="card"><h3>Акты испытаний и протоколы <span class="mut small" style="font-weight:400">необязательно</span><span class="r">${B(ic("plus") + "Документ", "rowAdd", `data-ent="act" data-id="${a.id}" data-p="tests" data-k="test"`, "sm")}</span></h3>
  ${
    a.tests.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th style="width:120px">Номер</th><th style="width:150px">Дата</th><th>Файл</th><th style="width:40px"></th></tr></thead><tbody>${a.tests
          .map(
            (
              t,
            ) => `<tr><td><input value="${esc(t.name)}" placeholder="Акт испытания / протокол" data-ent="act" data-id="${a.id}" data-f="tests.#${t.id}.name"></td><td><input value="${esc(t.num)}" data-ent="act" data-id="${a.id}" data-f="tests.#${t.id}.num"></td><td><input type="date" value="${t.date}" data-ent="act" data-id="${a.id}" data-f="tests.#${t.id}.date"></td>
   <td><div class="row" style="flex-wrap:nowrap">${t.file ? `<span class="small">${esc(t.file)}</span><span class="t2 small">${t.pages} л.</span>` : '<span class="pill p-r">нет файла</span>'}${B(t.file ? "Заменить" : "Загрузить", "pickPdf", `data-ent="act" data-id="${a.id}" data-p="tests.#${t.id}"`, "sm ghost")}</div></td><td>${B(ic("trash"), "rowRm", `data-ent="act" data-id="${a.id}" data-p="tests" data-r="${t.id}" title="Удалить"`, "sm icon ghost")}</td></tr>`,
          )
          .join("")}</tbody></table></div>`
      : '<div class="small mut">Нет</div>'
  }</div>
  <div class="card"><h3>Фотофиксация <span class="mut small" style="font-weight:400">необязательно · фототаблица вшивается в том сразу после акта</span></h3>${photoEditor(a)}</div>
  <div class="alert al-b"><span class="grow">В графе «Приложения» акта будет указано: <b>${esc(appsText(a, s))}</b></span></div>`;
  }
  if (tab === "prev") {
    const k = "pv" + a.id;
    const spId = a.subs.includes(S.ui.f[k]) ? S.ui.f[k] : a.subs[0];
    const sp = spOf(s, spId);
    body = `<div class="row mb">${a.subs.length > 1 ? a.subs.map((id) => `<span class="chk${id === spId ? " on" : ""}" data-a="setUi" data-k="${k}" data-v="${id}">${esc(spOf(s, id)?.name)}</span>`).join("") : `<span class="mut small">${esc(sp?.name || "")}</span>`}<span class="grow"></span>${B(ic("download") + "Сформировать DOCX", "stub", 'data-t="Формирование DOCX по шаблону профиля"')}${B("Печать", "stub", 'data-t="Печать акта"')}</div>
  ${sp ? aosrHtml(a, p, s, sp) : '<div class="empty">Акт не входит ни в один комплект — отметьте подпрофиль на вкладке «Основное».</div>'}`;
  }
  return `<div class="page">${hdr(
    esc(a.num) +
      ' <span class="mut" style="font-weight:500">' +
      esc(cut(a.works || "Новый акт", 64)) +
      "</span>",
    `${stP(a.status)}<span>${a.type === "АООК" ? "Акт освидетельствования ответственных конструкций" : "Акт освидетельствования скрытых работ"}</span>${a.updated ? "<span>· изменён " + esc(a.updated) + (a.updatedBy ? ", " + esc(a.updatedBy) : "") + "</span>" : ""}`,
    B(
      ic("folder"),
      "showInFolder",
      `data-path="${esc(winPath([objDir(p), sysDir(s), actDir(a)]))}" title="Показать папку акта"`,
      "icon",
    ) +
      B(ic("copy") + "Дублировать", "dup", `data-id="${a.id}"`) +
      B(
        ic("trash"),
        "del",
        `data-ent="act" data-id="${a.id}" title="Удалить акт"`,
        "icon",
      ),
    `<a href="#/p/${p.id}">${esc(p.name)}</a> / <a href="#/s/${s.id}">${esc(s.code)}</a>`,
  )}
 ${tabs(base, tab, [
   ["main", "Основное"],
   ["mat", "Материалы и АИК", a.materials.length],
   [
     "att",
     "Схемы, скан, фото",
     a.schemes.length +
       a.tests.length +
       a.photos.length +
       (a.scan?.file ? 1 : 0) || "",
   ],
   ["prev", "Предпросмотр"],
   ["files", "Файлы"],
 ])}${body}</div>`;
};
function photoEditor(a) {
  const n = photoSheets(a);
  return `<div class="row mb">${B(ic("photo") + "Загрузить фото", "photoAdd", `data-id="${a.id}"`, "sm")}${a.photos.length ? B("Подписи автоматически", "photoAuto", `data-id="${a.id}"`, "sm ghost") + B(ic("eye") + "Предпросмотр фототаблицы", "photoPrev", `data-id="${a.id}"`, "sm ghost") : ""}<span class="grow"></span>${
    a.photos.length
      ? F("", "act", a.id, "photoLayout", a.photoLayout, {
          opts: [
            [1, "1 фото на листе"],
            [2, "2 фото на листе"],
            [4, "4 фото на листе"],
          ],
          rr: 1,
          style: "width:170px",
        })
      : ""
  }</div>
 ${a.photos.length ? `<div class="phg">${a.photos.map((ph, i) => `<div class="pht"><div class="img"${ph.img ? ` style="background-image:url(${ph.img})"` : ""}>${ph.img ? "" : "Фото " + (i + 1)}</div><textarea data-ent="act" data-id="${a.id}" data-f="photos.#${ph.id}.cap" placeholder="Фото N. Что, где, дата">${esc(ph.cap)}</textarea><div class="row">${mvB("act", a.id, "photos", i)}<span class="grow"></span>${B("Заменить", "photoRepl", `data-id="${a.id}" data-p="${ph.id}"`, "sm ghost")}${B(ic("trash"), "rowRm", `data-ent="act" data-id="${a.id}" data-p="photos" data-r="${ph.id}" title="Удалить фото"`, "sm icon ghost")}</div></div>`).join("")}</div><div class="small mut mt">Фототаблица: ${n} л. Фототаблица учитывается отдельным приложением к акту.</div>` : '<div class="small mut">Фотографий нет.</div>'}`;
}
function sigLine(a, sp, i) {
  const x = person(signer(a, sp, i));
  return x
    ? `${esc(x.position)} ${esc(org(x.orgId)?.short || "")} ${esc(x.fioShort)}, ${esc(x.authority)}${x.nrs ? ", идентификационный номер в НРС " + esc(x.nrs) : ""}`
    : '<span class="miss">не назначен</span>';
}
function pl(v, cap) {
  return `<div class="pl">${v || '<span class="miss">не заполнено</span>'}</div>${cap ? `<div class="pc">(${cap})</div>` : ""}`;
}
function aosrHtml(a, p, s, sp) {
  const isK = a.type === "АООК";
  const pf = prof(sp.profileId);
  const mats = a.materials
    .map((id) => {
      const x = pMat(p, id);
      if (!x) return '<span class="miss">[удалённый материал]</span>';
      const d = mDocs(x);
      return (
        esc(mName(x)) +
        (d.length
          ? " (" +
            d
              .map((q) => `${esc(q.type)} № ${esc(q.num)} от ${fmtD(q.date)}`)
              .join("; ") +
            ")"
          : ' <span class="miss">(нет документов качества)</span>')
      );
    })
    .join("; ");

  const R = [
    "должность, фамилия, инициалы, реквизиты документа о представительстве",
    "",
  ];
  return `<div class="paper"><div><b>Объект капитального строительства</b></div>${pl(esc(p.name) + (p.address ? ", " + esc(p.address) : ""), "наименование, почтовый или строительный адрес объекта капитального строительства")}
 <div><b>Застройщик (технический заказчик)</b></div>${pl(esc(p.developer) + (p.techCustomer ? "; " + esc(p.techCustomer) : ""), "наименование, ОГРН, ИНН, почтовые реквизиты")}
 <div><b>Лицо, осуществляющее строительство</b></div>${pl(esc(p.genContractor), "наименование, номер и дата выдачи свидетельства о допуске, ОГРН, ИНН")}
 <div><b>Лицо, осуществляющее подготовку проектной документации</b></div>${pl(esc(p.designOrg), "наименование, ОГРН, ИНН, почтовые реквизиты")}
 <h2>АКТ</h2><div class="c"><b>${isK ? "освидетельствования ответственных конструкций" : "освидетельствования скрытых работ"}</b></div>
 <table style="margin:8px 0"><tr><td>№ <u>${esc(a.num)}</u></td><td style="text-align:right">«${fmtD(a.date)}»</td></tr></table>
 ${DOC_ROLES.map((r, i) => `<div class="small">${esc(r)}</div>${pl(sigLine(a, sp, i), i < 2 ? R[0] : "")}`).join("")}
 <div style="margin-top:8px">произвели осмотр ${isK ? "конструкций" : "работ"}, выполненных ${esc(org(person(signer(a, sp, 4))?.orgId)?.short || "—")}, и составили настоящий акт о нижеследующем:</div>
 <div>1. К освидетельствованию предъявлены следующие ${isK ? "конструкции" : "работы"}:</div>${pl(esc(a.works) + (a.place ? ". " + esc(a.place) : ""), "наименование скрытых работ")}
 <div>2. Работы выполнены по проектной документации:</div>${pl(esc(a.rd), "номер, другие реквизиты чертежа, наименование проектной документации")}
 <div>3. При выполнении работ применены:</div>${pl(mats, "наименование строительных материалов (изделий) со ссылкой на сертификаты или другие документы")}
 <div>4. Предъявлены документы, подтверждающие соответствие работ предъявляемым к ним требованиям:</div>${pl(esc(appsText(a, s)).replace(/\n/g, "<br>"), "исполнительные схемы и чертежи, результаты экспертиз, обследований, испытаний")}
 <div>5. Даты: начала работ <u>${fmtD(a.start)}</u> окончания работ <u>${fmtD(a.end)}</u></div>
 <div style="margin-top:6px">6. Работы выполнены в соответствии с:</div>${pl(esc(a.norms), "наименования и структурные единицы технических регламентов, иных нормативных правовых актов")}
 <div>7. Разрешается производство последующих работ по:</div>${pl(esc(a.next), "наименование работ, конструкций, участков сетей инженерно-технического обеспечения")}
 <div style="margin-top:6px">Дополнительные сведения: ____________________</div><div>Акт составлен в ___ экземплярах.</div><div>Приложения: ${esc(appsText(a, s))}</div>
 <table style="margin-top:12px">${ROLE_SH.map((r, i) => {
   const x = person(signer(a, sp, i));
   return `<tr><td style="width:55%;padding:3px 0">${esc(r)}</td><td style="border-bottom:1px solid #000;padding:3px 4px">${x ? esc(x.fioShort) : '<span class="miss">—</span>'}</td><td style="width:80px;border-bottom:1px solid #000">${x?.sign ? `<img src="${x.sign}" style="height:22px">` : ""}</td></tr>`;
 }).join("")}</table>
 <div class="pc" style="text-align:left;margin-top:10px">Комплект: ${esc(sp.name)} · профиль: ${esc(pf ? pf.name : "—")} · шаблон: ${esc(pf ? (pf.templates.map(tpl).find((t) => t && t.type === a.type) || {}).name || "не найден" : "—")}</div></div>`;
}

/* ---- АИК ---- */
V.k = (r) => {
  const c = ctx("aik", r[1]);
  const k = c.o,
    s = c.s,
    p = c.p;
  if (!k) return V.home();
  const m = pMat(p, k.materialId);
  const used = s.acts.filter((a) => Object.values(a.aikLinks).includes(k.id));
  return `<div class="page">${hdr(esc(k.num) + ' <span class="mut" style="font-weight:500">Акт входного контроля</span>', stP(k.status) + "<span>" + esc(mName(m) || "материал удалён") + "</span>", B(ic("eye") + "Предпросмотр", "aikPrev", `data-id="${k.id}"`) + B(ic("trash"), "del", `data-ent="aik" data-id="${k.id}" title="Удалить"`, "icon"), `<a href="#/p/${p.id}">${esc(p.name)}</a> / <a href="#/s/${s.id}/aik">${esc(s.code)} · АИК</a>`)}
 <div class="card"><h3>Реквизиты</h3><div class="g4">${F("Номер", "aik", k.id, "num", k.num, { rr: 1 })}${F("Дата", "aik", k.id, "date", k.date, { type: "date", rr: 1 })}${F("Статус", "aik", k.id, "status", k.status, { opts: ["В работе", "Готово"], rr: 1 })}${F("Количество (необязательно)", "aik", k.id, "qty", k.qty)}
  ${F("Материал объекта", "aik", k.id, "materialId", k.materialId, { opts: [["", "— выберите —"], ...p.materials.map((x) => [x.id, mName(x)])], rr: 1, style: "grid-column:span 2" })}${F("Примечание", "aik", k.id, "note", k.note, { style: "grid-column:span 2" })}</div></div>
 <div class="card"><h3>Документы качества материала<span class="r">${m ? `<a class="small" href="#/m/${m.id}">Открыть материал</a>` : ""}</span></h3>${docsTable(m, false)}</div>
 <div class="card"><h3>Привязан к актам</h3>${used.length ? used.map((a) => `<a class="btn sm" href="#/a/${a.id}" style="margin:0 6px 6px 0">${esc(a.num)}</a>`).join("") : '<div class="small mut">Не привязан ни к одному акту</div>'}</div>
 ${remarksCard("aik", k.id, k.remarks)}</div>`;
};
function docsTable(m, ed, ent, id) {
  if (!m) return '<div class="small mut">—</div>';
  const docs = mDocs(m);
  if (!ed)
    return docs.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th>Тип</th><th>Номер</th><th>Дата</th><th>Файл</th></tr></thead><tbody>${docs.map((d) => `<tr><td>${esc(d.type)}</td><td>${esc(d.num)}</td><td class="t2">${fmtD(d.date)}</td><td class="t2">${d.file ? esc(d.file) + " · " + d.pages + " л." : '<span class="pill p-r">нет файла</span>'}</td></tr>`).join("")}</tbody></table></div>`
      : '<div class="alert al-a" style="margin:0">Документов качества нет</div>';
  const A_ = `data-ent="${ent}" data-id="${id}"`;
  return `${
    docs.length
      ? `<div class="tw"><table class="tbl"><thead><tr><th style="width:220px">Тип</th><th>Номер</th><th style="width:150px">Дата</th><th>Файл</th><th style="width:40px"></th></tr></thead><tbody>${docs
          .map(
            (
              d,
            ) => `<tr><td>${F("", ent, id, "docs.#" + d.id + ".type", d.type, { opts: QDOC })}</td><td><input value="${esc(d.num)}" ${A_} data-f="docs.#${d.id}.num"></td><td><input type="date" value="${d.date}" ${A_} data-f="docs.#${d.id}.date"></td>
  <td><div class="row" style="flex-wrap:nowrap">${d.file ? `<span class="small" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:210px">${esc(d.file)}</span><span class="t2 small">${d.pages} л.</span>` : '<span class="pill p-r">нет файла</span>'}${B(d.file ? "Заменить" : "Загрузить", "pickPdf", `${A_} data-p="docs.#${d.id}"`, "sm ghost")}</div></td><td>${B(ic("trash"), "rowRm", `${A_} data-p="docs" data-r="${d.id}" title="Удалить"`, "sm icon ghost")}</td></tr>`,
          )
          .join("")}</tbody></table></div>`
      : '<div class="small mut mb">Документов пока нет</div>'
  }
 <div class="mt">${B(ic("plus") + "Документ", "rowAdd", `${A_} data-p="docs" data-k="doc"`, "sm")}</div>`;
}

/* ---- Материал объекта ---- */
V.m = (r) => {
  const c = ctx("mat", r[1]);
  const m = c.o,
    p = c.p;
  if (!m) return V.home();
  const b = baseOf(m);
  const used = p.systems.flatMap((s) =>
    s.acts.filter((a) => a.materials.includes(m.id)).map((a) => ({ a, s })),
  );
  const ks = p.systems.flatMap((s) =>
    s.aik.filter((k) => k.materialId === m.id).map((k) => ({ k, s })),
  );
  let body;
  if (m.baseId) {
    body = b
      ? `<div class="alert al-b"><span class="grow">Сведения и документы берутся из базы паспортов и редактируются там. Изменения в базе сразу применяются во всех объектах, где используется этот паспорт.</span>${B("Открыть в базе", "nav", `data-h="#/lib/base/${b.id}"`, "sm")}${B("Отвязать (сделать копию)", "matUnlink", `data-id="${m.id}"`, "sm")}</div>
  <div class="card"><h3>Сведения</h3><div class="kv"><div>Наименование</div><div>${esc(b.name)}</div><div>Категория</div><div>${esc(b.category || "—")}</div><div>Марка</div><div>${esc(b.brand || "—")}</div><div>Производитель</div><div>${esc(b.maker || "—")}</div></div></div>
  <div class="card"><h3>Документы качества</h3>${docsTable(m, false)}</div>`
      : `<div class="alert al-r"><span class="grow">Позиция базы паспортов удалена.</span>${B("Сделать своим материалом", "matUnlink", `data-id="${m.id}"`, "sm")}</div>`;
  } else
    body = `<datalist id="catList">${[...new Set(S.lib.base.map((x) => x.category))].map((x) => `<option value="${esc(x)}">`).join("")}</datalist>
  <div class="card"><h3>Сведения<span class="r">${B(ic("up") + "Добавить в базу паспортов", "matToBase", `data-id="${m.id}"`, "sm ghost")}</span></h3><div class="g2">${F("Наименование", "mat", m.id, "name", m.name, { req: 1, span: 1, rr: 1 })}${F("Категория", "mat", m.id, "category", m.category, { list: "catList" })}${F("Марка", "mat", m.id, "brand", m.brand)}${F("Производитель", "mat", m.id, "maker", m.maker)}${F("Примечание", "mat", m.id, "note", m.note)}</div></div>
  <div class="card"><h3>Документы качества</h3>${docsTable(m, true, "mat", m.id)}</div>`;
  body += `<div class="cols"><div class="card"><h3>Применён в актах</h3>${used.length ? used.map(({ a, s }) => `<a class="btn sm" href="#/a/${a.id}" style="margin:0 6px 6px 0">${esc(s.code)} · ${esc(a.num)}</a>`).join("") : '<div class="small mut">Не используется</div>'}</div>
  <div class="card"><h3>Входной контроль</h3>${ks.length ? ks.map(({ k, s }) => `<a class="btn sm" href="#/k/${k.id}" style="margin:0 6px 6px 0">${esc(s.code)} · ${esc(k.num)}</a>`).join("") : '<div class="small mut">АИК нет</div>'}</div></div>`;
  return `<div class="page">${hdr(esc(mName(m) || "Новый материал"), m.baseId ? '<span class="pill p-b">Связан с базой паспортов</span>' : '<span class="pill p-n">Свой материал объекта</span>', B(ic("trash"), "del", `data-ent="mat" data-id="${m.id}" title="Убрать из объекта"`, "icon"), `<a href="#/p/${p.id}">${esc(p.name)}</a> / <a href="#/p/${p.id}/mats">Материалы и паспорта</a>`)}${body}</div>`;
};

/* ---- Журнал ---- */
V.j = (r) => {
  const c = ctx("jr", r[1]);
  const j = c.o,
    s = c.s,
    p = c.p;
  if (!j) return V.home();
  const custom = j.kind.startsWith("Пользовательский");
  const A_ = `data-ent="jr" data-id="${j.id}"`;
  let body = `<div class="card"><h3>Параметры</h3><div class="g3">${F("Наименование", "jr", j.id, "name", j.name, { req: 1, rr: 1 })}${F("Вид журнала", "jr", j.id, "kind", j.kind, { opts: Object.keys(JKINDS), rr: 1 })}<div class="fld"><span>Способ ведения</span><div class="row" style="min-height:36px"><span class="chk${j.mode === "A" ? " on" : ""}" data-a="jMode" data-id="${j.id}" data-v="A">Ввод записей</span><span class="chk${j.mode === "B" ? " on" : ""}" data-a="jMode" data-id="${j.id}" data-v="B">Готовый PDF</span></div></div></div></div>`;
  if (j.mode === "A") {
    if (custom)
      body += `<div class="card"><h3>Колонки</h3><div class="row">${j.cols.map((x, i) => `<span class="row" style="gap:2px"><input value="${esc(x)}" ${A_} data-f="cols.${i}" data-rr="1" style="width:170px">${B("×", "jColRm", `data-id="${j.id}" data-i="${i}" title="Удалить колонку"`, "sm icon ghost")}</span>`).join("")}${B(ic("plus") + "Колонка", "jColAdd", `data-id="${j.id}"`, "sm")}</div></div>`;
    body += `<div class="card"><h3>Записи <span class="pill p-n">${j.rows.length}</span><span class="r row">${j.kind.startsWith("Общий") ? B("Заполнить из актов", "jFromActs", `data-id="${j.id}"`, "sm ghost") : ""}${B(ic("plus") + "Запись", "jRowAdd", `data-id="${j.id}"`, "sm")}</span></h3>
  ${j.rows.length ? `<div class="tw" style="max-height:460px"><table class="tbl"><thead><tr><th style="width:40px">№</th>${j.cols.map((x) => `<th>${esc(x)}</th>`).join("")}<th style="width:40px"></th></tr></thead><tbody>${j.rows.map((row, i) => `<tr><td class="num t2">${i + 1}</td>${j.cols.map((x, ci) => `<td><input value="${esc(row.c[ci] || "")}" ${A_} data-f="rows.#${row.id}.c.${ci}"></td>`).join("")}<td>${B(ic("trash"), "rowRm", `${A_} data-p="rows" data-r="${row.id}" title="Удалить"`, "sm icon ghost")}</td></tr>`).join("")}</tbody></table></div>` : '<div class="small mut">Записей нет</div>'}
  <div class="row mt">${B("Сформировать PDF по РД-11-05-2007", "stub", 'data-t="Формирование PDF журнала"', "pri")}</div></div>`;
  } else
    body += `<div class="card"><h3>Готовый PDF журнала<span class="r">${B(ic("up") + (j.file ? "Заменить PDF" : "Прикрепить PDF"), "pickPdf", `${A_} data-p=""`, "sm")}</span></h3>${fileBox(j.file, j.pages, "")}<div class="small mut mt">При сборке ${s ? "тома системы" : "Тома 1"} PDF вставляется как есть, в реестр добавляется строка «${esc(j.name)}, ${j.pages || "?"} л.»</div></div>`;
  body += remarksCard("jr", j.id, j.remarks);
  return `<div class="page">${hdr(esc(j.name), esc(j.kind) + " · " + (s ? "система " + esc(s.code) : "объект"), B(ic("trash"), "del", `data-ent="jr" data-id="${j.id}" title="Удалить журнал"`, "icon"), `<a href="#/p/${p.id}">${esc(p.name)}</a> / ` + (s ? `<a href="#/s/${s.id}/jr">${esc(s.code)} · Журналы</a>` : `<a href="#/p/${p.id}/ozhr">Журнал работ</a>`))}${body}</div>`;
};

/* ---- Справочники ---- */
V.lib = (r) => {
  const sec = r[1] || "orgs";
  if (["orgs", "people", "sign", "orders"].includes(sec))
    return libOrgs(sec, r[2]);
  if (sec === "base") return libBase(r[2]);
  return libProfiles(sec, r[2]);
};
function libOrgs(tab, sel) {
  let body = "";
  if (tab === "orgs") {
    const o = org(sel);
    body = `<div class="row mb"><span class="mut small grow">Организации общие для всех объектов.</span>${B(ic("plus") + "Организация", "libNew", 'data-k="org"', "pri")}</div>
  <div class="tw"><table class="tbl"><thead><tr><th>Краткое наименование</th><th>Роль</th><th>ИНН</th><th>СРО</th><th class="num">Представителей</th></tr></thead><tbody>${S.lib.orgs.map((x) => `<tr class="cl${x.id === sel ? " sel" : ""}" data-a="nav" data-h="#/lib/orgs/${x.id}"><td><b style="font-weight:550">${esc(x.short)}</b></td><td class="t2">${esc(x.role)}</td><td class="t2">${esc(x.inn)}</td><td class="t2">${esc(x.sro || "—")}</td><td class="num">${S.lib.people.filter((p) => p.orgId === x.id).length}</td></tr>`).join("")}</tbody></table></div>
  ${o ? `<div class="card mt" style="margin-top:16px"><h3>${esc(o.short)}<span class="r">${B(ic("trash"), "del", `data-ent="org" data-id="${o.id}" title="Удалить"`, "sm icon ghost")}</span></h3><div class="g3">${F("Полное наименование", "org", o.id, "full", o.full, { span: 1 })}${F("Краткое наименование", "org", o.id, "short", o.short, { rr: 1 })}${F("Роль", "org", o.id, "role", o.role, { opts: ORG_ROLES, rr: 1 })}${F("ИНН", "org", o.id, "inn", o.inn)}${F("ОГРН", "org", o.id, "ogrn", o.ogrn)}${F("КПП", "org", o.id, "kpp", o.kpp || "")}${F("Телефон", "org", o.id, "phone", o.phone || "")}${F("Электронная почта", "org", o.id, "email", o.email || "")}${F("Членство в СРО", "org", o.id, "sro", o.sro)}${F("Адрес", "org", o.id, "address", o.address, { span: 1 })}</div></div>` : ""}`;
  }
  if (tab === "people") {
    const x = person(sel);
    body = `<div class="row mb"><span class="mut small grow">Представители общие для всех объектов. Подписанты в подпрофилях и актах выбираются из этого списка.</span>${B(ic("plus") + "Представитель", "libNew", 'data-k="per"', "pri")}</div>
  <div class="tw"><table class="tbl"><thead><tr><th>ФИО</th><th>Должность</th><th>Организация</th><th>Роль в актах</th><th>НРС</th></tr></thead><tbody>${S.lib.people.map((p) => `<tr class="cl${p.id === sel ? " sel" : ""}" data-a="nav" data-h="#/lib/people/${p.id}"><td><b style="font-weight:550">${esc(p.fioShort)}</b></td><td class="t2">${esc(p.position)}</td><td class="t2">${esc(org(p.orgId)?.short || "—")}</td><td class="t2">${esc(ROLE_SH[p.docRole] || "—")}</td><td class="t2">${esc(p.nrs || "—")}</td></tr>`).join("")}</tbody></table></div>
  ${
    x
      ? `<div class="card mt" style="margin-top:16px"><h3>${esc(x.fioShort)}<span class="r">${B(ic("trash"), "del", `data-ent="per" data-id="${x.id}" title="Удалить"`, "sm icon ghost")}</span></h3><div class="g3">${F("ФИО полностью", "per", x.id, "fio", x.fio)}${F("Фамилия, инициалы", "per", x.id, "fioShort", x.fioShort, { rr: 1 })}${F("Должность", "per", x.id, "position", x.position, { rr: 1 })}${F("Организация", "per", x.id, "orgId", x.orgId, { opts: S.lib.orgs.map((o) => [o.id, o.short]), rr: 1 })}${F("Роль в актах", "per", x.id, "docRole", x.docRole, { opts: ROLE_SH.map((t, i) => [i, t]), rr: 1 })}${F("Номер в НРС", "per", x.id, "nrs", x.nrs)}${F("Документ о полномочиях", "per", x.id, "authority", x.authority, { span: 1 })}
   <div class="fld"><span>Изображение подписи</span><div class="row">${x.sign ? `<img src="${x.sign}" style="height:32px;border:1px solid var(--line);border-radius:6px;padding:2px 6px;background:#fff">` : ""}${B(x.sign ? "Заменить" : "Загрузить PNG", "signPick", `data-id="${x.id}"`, "sm")}</div></div></div></div>`
      : ""
  }`;
  }
  if (tab === "sign") {
    const types = Object.keys(S.lib.signMatrix);
    body = `<div class="mut small mb">Кто может подписывать документы каждого типа. Списки выбора подписантов фильтруются по этой матрице.</div><div class="tw"><table class="tbl"><thead><tr><th>Представитель</th>${types.map((t) => `<th style="text-align:center">${esc(t)}</th>`).join("")}</tr></thead><tbody>${S.lib.people.map((p) => `<tr><td>${esc(p.fioShort)} <span class="t2">${esc(p.position)}</span></td>${types.map((t) => `<td style="text-align:center"><input type="checkbox" data-a="signTog" data-t="${esc(t)}" data-p="${p.id}" ${S.lib.signMatrix[t].includes(p.id) ? "checked" : ""}></td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  if (tab === "orders")
    body = `<div class="row mb"><span class="mut small grow">Приказы, доверенности, выписки СРО — попадают в Том 1 каждого объекта.</span>${B(ic("plus") + "Документ", "libNew", 'data-k="ord"', "pri")}</div>
  <div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th style="width:100px">Номер</th><th style="width:150px">Дата</th><th style="width:190px">Организация</th><th>Файл</th><th style="width:40px"></th></tr></thead><tbody>${S.lib.orders
    .map(
      (
        o,
      ) => `<tr><td><input value="${esc(o.name)}" data-ent="ord" data-id="${o.id}" data-f="name"></td><td><input value="${esc(o.num)}" data-ent="ord" data-id="${o.id}" data-f="num"></td><td><input type="date" value="${o.date}" data-ent="ord" data-id="${o.id}" data-f="date"></td><td>${F("", "ord", o.id, "orgId", o.orgId, { opts: S.lib.orgs.map((x) => [x.id, x.short]) })}</td>
  <td><div class="row" style="flex-wrap:nowrap">${o.file ? `<span class="small">${esc(o.file)}</span>` : '<span class="pill p-r">нет файла</span>'}${B(o.file ? "Заменить" : "Загрузить", "pickPdf", `data-ent="ord" data-id="${o.id}" data-p=""`, "sm ghost")}</div></td><td>${B(ic("trash"), "del", `data-ent="ord" data-id="${o.id}" title="Удалить"`, "sm icon ghost")}</td></tr>`,
    )
    .join("")}</tbody></table></div>`;
  return `<div class="page">${hdr("Организации и подписанты", "Общие для всех объектов")}${tabs(
    "#/lib",
    tab,
    [
      ["orgs", "Организации", S.lib.orgs.length],
      ["people", "Представители", S.lib.people.length],
      ["sign", "Матрица подписантов"],
      ["orders", "Приказы и допуски", S.lib.orders.length],
    ],
  )}${body}</div>`;
}
function baseUse(b) {
  return S.projects.filter((p) => p.materials.some((m) => m.baseId === b.id));
}
function libBase(sel) {
  const b = S.lib.base.find((x) => x.id === sel);
  const q = S.ui.f.bq || "";
  const L = S.lib.base.filter(
    (x) =>
      !q ||
      norm(
        x.name + " " + x.maker + " " + x.docs.map((d) => d.num).join(" "),
      ).includes(norm(q)),
  );
  let card = "";
  if (b) {
    const use = baseUse(b);
    card = `<div class="card"><h3>${esc(b.name)}<span class="r row">${B(ic("link") + "Добавить в объект", "baseToProj", `data-id="${b.id}"`, "sm")}${B(ic("trash"), "del", `data-ent="base" data-id="${b.id}" title="Удалить из базы"`, "sm icon ghost")}</span></h3>
  ${use.length ? `<div class="alert al-b">Используется в объектах: ${use.map((p) => `<a href="#/p/${p.id}/mats">${esc(p.name)}</a>`).join(", ")}. Изменения применяются везде.</div>` : ""}
  <div class="g2">${F("Наименование", "base", b.id, "name", b.name, { span: 1, rr: 1 })}${F("Категория", "base", b.id, "category", b.category)}${F("Марка", "base", b.id, "brand", b.brand)}${F("Производитель", "base", b.id, "maker", b.maker, { span: 1 })}</div>
  <div class="small mut" style="margin:16px 0 8px;font-weight:600">Документы качества</div>${docsTable(b, true, "base", b.id)}</div>`;
  }
  return `<div class="page">${hdr("База паспортов", "Стандартные паспорта и сертификаты. В объект добавляются как связанные материалы", B(ic("plus") + "Паспорт", "libNew", 'data-k="base"', "pri"))}
 <div class="row mb">${F("", "ui", "", "f.bq", q, { rr: 1, ph: "Наименование, производитель или № документа", style: "width:360px" })}<span class="mut small">${L.length} из ${S.lib.base.length}</span></div>
 <div class="${b ? "cols" : ""}"><div class="tw"><table class="tbl"><thead><tr><th>Наименование</th><th>Документы</th><th class="num">Объектов</th></tr></thead><tbody>${L.map((x) => `<tr class="cl${x.id === sel ? " sel" : ""}" data-a="nav" data-h="#/lib/base/${x.id}"><td><b style="font-weight:550">${esc(x.name)}</b><div class="t2">${esc(x.category)} · ${esc(x.maker || "—")}</div></td><td>${x.docs.map((d) => `<span class="pill p-n" style="margin:1px">${esc(d.type)}</span>`).join(" ") || '<span class="pill p-r">нет</span>'}</td><td class="num">${baseUse(x).length}</td></tr>`).join("")}</tbody></table></div>${card}</div></div>`;
}
function libProfiles(tab, sel) {
  let body = "";
  if (tab === "profiles") {
    const x = prof(sel);
    body = `<div class="row mb"><span class="mut small grow">Профиль — требования конкретного заказчика к оформлению: шаблоны, правило размещения документов качества, обязательные поля. Подпрофиль системы ссылается на профиль заказчика.</span>${B(ic("plus") + "Профиль", "libNew", 'data-k="pf"', "pri")}</div>
  <div class="${x ? "cols" : ""}"><div class="tw"><table class="tbl"><thead><tr><th>Профиль</th><th>Дата</th><th>Документы качества</th><th class="num">Подпрофилей</th></tr></thead><tbody>${S.lib.profiles.map((p) => `<tr class="cl${p.id === sel ? " sel" : ""}" data-a="nav" data-h="#/lib/profiles/${p.id}"><td><b style="font-weight:550">${esc(p.name)}</b></td><td><span class="t2">${fmtD(p.date)}</span></td><td class="t2">${esc(QRULES[p.quality])}</td><td class="num">${pfUse(p).length}</td></tr>`).join("")}</tbody></table></div>
  ${
    x
      ? `<div class="card"><h3>${esc(x.name)} ·<span class="r row">${B(ic("trash"), "del", `data-ent="pf" data-id="${x.id}" title="Удалить"`, "sm icon ghost")}</span></h3>
   ${
     pfUse(x).length
       ? `<div class="alert al-b">Используется: ${pfUse(x)
           .map((u) => esc(u.p.name + " · " + u.sp.name))
           .join("; ")}</div>`
       : ""
   }
   <div class="g2">${F("Наименование", "pf", x.id, "name", x.name, { span: 1, rr: 1 })}${F("Документы качества", "pf", x.id, "quality", x.quality, { opts: Object.entries(QRULES), rr: 1 })}${F("Именование файлов", "pf", x.id, "naming", x.naming)}${F("Особые требования", "pf", x.id, "extra", x.extra, { rows: 2, span: 1 })}</div>
   <div class="small mut" style="margin:16px 0 8px;font-weight:600">Обязательные поля акта</div><div class="row">${Object.entries(
     FIELD_NAMES,
   )
     .map(
       ([k, t]) =>
         `<span class="chk${x.reqFields.includes(k) ? " on" : ""}" data-a="pfArr" data-id="${x.id}" data-arr="reqFields" data-v="${k}">${esc(t)}</span>`,
     )
     .join("")}</div>
   <div class="small mut" style="margin:16px 0 8px;font-weight:600">Обязательные документы (нужен шаблон)</div><div class="row">${TPL_TYPES.map((t) => `<span class="chk${x.reqDocs.includes(t) ? " on" : ""}" data-a="pfArr" data-id="${x.id}" data-arr="reqDocs" data-v="${esc(t)}">${esc(t)}</span>`).join("")}</div>
   <div class="small mut" style="margin:16px 0 8px;font-weight:600">Шаблоны профиля</div><div class="lst">${S.lib.templates.map((t) => `<label><input type="checkbox" data-a="pfArr" data-id="${x.id}" data-arr="templates" data-v="${t.id}" ${x.templates.includes(t.id) ? "checked" : ""}><span class="grow">${esc(t.name)}</span><span class="pill p-n">${esc(t.type)}</span></label>`).join("")}</div></div>`
      : ""
  }</div>`;
  }
  if (tab === "templates") {
    const known = knownTags();
    body = `<div class="row mb"><span class="mut small grow">Шаблоны Word (.docx) с тегами вида <code class="tag">{{АОСР.Номер}}</code>. При загрузке теги извлекаются из файла и сверяются со справочником.</span>${B(ic("up") + "Загрузить шаблон .docx", "tplAdd", "", "pri")}</div>
  <div class="tw"><table class="tbl"><thead><tr><th>Шаблон</th><th>Тип</th><th>Теги</th><th>Файл</th><th style="width:80px"></th></tr></thead><tbody>${S.lib.templates
    .map((t) => {
      const unk = t.tags.filter((x) => !known.has(x));
      return `<tr><td><input value="${esc(t.name)}" data-ent="tpl" data-id="${t.id}" data-f="name">${t.locked ? '<div class="t2" style="margin-top:3px">Системный шаблон по РД</div>' : ""}</td><td style="width:170px">${F("", "tpl", t.id, "type", t.type, { opts: TPL_TYPES, rr: 1 })}</td><td class="t2">${t.tags.length} тегов${unk.length ? `<br><span class="pill p-r">неизвестные: ${esc(unk.join(", "))}</span>` : ""}</td><td class="t2">${esc(t.file)}<br>${fmtD(t.date)}</td><td><div class="row" style="flex-wrap:nowrap;gap:4px">${B(ic("up"), "tplReplace", `data-id="${t.id}" title="Заменить файл"`, "sm icon ghost")}${t.locked ? "" : B(ic("trash"), "del", `data-ent="tpl" data-id="${t.id}" title="Удалить"`, "sm icon ghost")}</div></td></tr>`;
    })
    .join("")}</tbody></table></div>`;
  }
  if (tab === "tags") {
    const all = S.projects.flatMap((p) =>
      p.systems.flatMap((s) => s.acts.map((a) => ({ a, s, p }))),
    );
    const cur = all.find((x) => x.a.id === S.ui.tagAct) || all[0];
    body = `<div class="row mb"><span class="mut small">Пример значений для акта:</span>${F("", "ui", "", "tagAct", cur?.a.id || "", { opts: all.map((x) => [x.a.id, x.p.name + " · " + x.s.code + " · " + x.a.num]), rr: 1, style: "width:360px" })}</div>
  <div class="tw"><table class="tbl"><thead><tr><th>Тег</th><th>Источник</th><th>Значение</th></tr></thead><tbody>${TAGS.map(([t, src, fn]) => `<tr><td><code class="tag">{{${t}}}</code></td><td class="t2">${esc(src)}</td><td class="small">${esc(cut(cur ? fn(cur.a, cur.p, cur.s) || "—" : "—", 110))}</td></tr>`).join("")}
  ${[...new Set(S.projects.flatMap((p) => p.extra.map((x) => "ДопПоля." + slug(x.k))))].map((t) => `<tr><td><code class="tag">{{${esc(t)}}}</code></td><td class="t2">Доп. реквизит объекта</td><td class="small">${esc(cur?.p.extra.find((x) => slug(x.k) === t)?.v || "—")}</td></tr>`).join("")}</tbody></table></div>`;
  }
  return `<div class="page">${hdr("Профили и шаблоны", "Требования заказчиков к оформлению ИД")}${tabs(
    "#/lib",
    tab,
    [
      ["profiles", "Профили заказчиков", S.lib.profiles.length],
      ["templates", "Шаблоны Word", S.lib.templates.length],
      ["tags", "Справочник тегов", TAGS.length],
    ],
  )}${body}</div>`;
}
function pfUse(pf) {
  const o = [];
  S.projects.forEach((p) =>
    p.systems.forEach((s) =>
      s.subprofiles.forEach((sp) => {
        if (sp.profileId === pf.id) o.push({ p, s, sp });
      }),
    ),
  );
  return o;
}
function knownTags() {
  return new Set(
    TAGS.map((x) => x[0]).concat(
      S.projects.flatMap((p) => p.extra.map((x) => "ДопПоля." + slug(x.k))),
    ),
  );
}

/* ---- Сборка тома ---- */

/* ---- Настройки ---- */
V.settings = (r) => {
  const tab = r[1] || "general";
  let body = "";
  if (tab === "general") {
    const users = {};
    S.history.forEach((h) => {
      if (!users[h.user]) users[h.user] = h.ts;
    });
    Object.values(S.locks)
      .flat()
      .forEach((l) => {
        if (!users[l.user])
          users[l.user] = fmtD(l.pulse.slice(0, 10)) + ", " + hm(l.pulse);
      });
    body = `<div class="card"><h3>Этот компьютер</h3><div class="g3">${F("Фамилия и инициалы", "app", "", "user", APP.user, { rr: 1 })}${F("Компьютер", "app", "", "pc", APP.pc, { rr: 1 })}<div class="fld"><span>Режим</span><div class="row" style="min-height:36px">${B(S.ui.ro ? "Включить редактирование" : "Только просмотр", "roToggle", "", "sm")}</div></div></div><div class="small mut mt">Хранится на компьютере, а не в базе. Используется в реквизитах приложения.</div></div>
  <div class="card"><h3>База</h3><div class="g2">${F("Название базы", "root", "", "meta.name", S.meta.name, { rr: 1 })}<div class="fld"><span>Папка на этом компьютере</span><div class="row" style="flex-wrap:nowrap"><input value="${esc(APP.current)}" readonly style="flex:1">${B(ic("folder"), "showInFolder", `data-path="${esc(APP.current)}" title="Показать в папке"`, "icon")}</div></div></div>
   <div class="g3 mt">${F("Хранить удалённое в корзине, дней", "app", "", "trashDays", APP.trashDays, { type: "number" })}<div class="fld"><span>Метки редактирования</span><div class="small" style="min-height:36px;display:flex;align-items:center">пульс каждые ${PULSE_MIN} мин · брошенной считается через ${STALE_MIN} мин</div></div><div class="fld"><span>&nbsp;</span><div class="row">${B("Сменить базу", "baseSwitch", "", "sm")}${B("Папка базы", "nav", 'data-h="#/files"', "sm ghost")}</div></div></div></div>
  <div class="card"><h3>Кто работает с базой</h3><div class="tw"><table class="tbl"><thead><tr><th>Пользователь</th><th>Последняя активность</th><th>Сейчас</th></tr></thead><tbody>${Object.entries(
    users,
  )
    .map(([u, t]) => {
      const ls = Object.entries(S.locks).filter(([k, L]) =>
        L.some((l) => l.user === u && isFresh(l)),
      );
      return `<tr><td>${esc(u)}${u === APP.user ? ' <span class="pill p-b">вы</span>' : ""}</td><td class="t2">${esc(t)}</td><td class="t2">${ls.length ? "редактирует: " + esc(ls.map(([k]) => lockName(k)).join(", ")) : "—"}</td></tr>`;
    })
    .join(
      "",
    )}</tbody></table></div><div class="small mut mt">Доступ к базе выдаётся через общий доступ к папке на Яндекс Диске — отдельных паролей в программе нет.</div></div>
  <div class="card"><h3>Совместная работа (имитация)</h3><div class="small mut">Откройте систему или акт и выберите в меню «⋯» справа вверху: одновременный захват, брошенная метка, изменение от коллеги, конфликт версий.</div></div>
  <div class="card"><h3>Для разработки</h3><div class="row">${B(ic("download") + "Экспорт данных в JSON", "exportJson", "", "sm")}${B(ic("up") + "Загрузить JSON", "importJson", "", "sm")}${B("Восстановить демо-данные", "resetDemo", "", "sm dng")}</div><div class="small mut mt">Прототип имитирует папку базы внутри браузера. В приложении (Python + Qt) данные — это файлы в папке на Яндекс Диске.</div></div>
  <div class="card"><h3>О прототипе</h3><div class="small mut">СтройИД · прототип интерфейса v3 по ТЗ v12.0. Локальное приложение, база — папка на Яндекс Диске. Структура: объект → системы → АОСР. Кнопки, требующие реальных файлов и системных окон, работают как заглушки.</div></div>`;
  }

  if (tab === "trash")
    body = `<div class="row mb"><span class="mut small grow">Удалённое переносится в папку «_Корзина» и хранится ${+APP.trashDays || 30} дней, затем очищается автоматически.</span>${S.trash.length ? B("Очистить корзину", "trEmpty", "", "sm dng") : ""}</div>
  ${S.trash.length ? `<div class="tw"><table class="tbl"><thead><tr><th>Элемент</th><th>Где</th><th>Удалён</th><th>Очистится</th><th style="width:210px"></th></tr></thead><tbody>${S.trash.map((t) => `<tr><td>${esc(cap1(entLabel(t.ent, t.item)).replace(/^./, (c) => c.toUpperCase()))}</td><td class="t2">${esc([proj(t.ctx?.pid)?.name, getEnt("sys", t.ctx?.sid)?.code].filter(Boolean).join(" · ") || "—")}</td><td class="t2">${esc(t.ts)} · ${esc(t.by)}</td><td class="t2">${t.iso ? "через " + Math.max(0, Math.ceil(((+APP.trashDays || 30) * 864e5 - (Date.now() - Date.parse(t.iso))) / 864e5)) + " дн." : "—"}</td><td><div class="row" style="flex-wrap:nowrap">${B("Восстановить", "trRestore", `data-id="${t.id}"`, "sm")}${B(ic("trash"), "trPurge", `data-id="${t.id}" title="Удалить навсегда"`, "sm icon ghost")}</div></td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">Корзина пуста</div>'}`;

  return `<div class="page">${hdr("Настройки", "")}${tabs("#/settings", tab, [
    ["general", "Общие"],
    ["trash", "Корзина", S.trash.length],
  ])}${body}</div>`;
};

/* ---- Поиск ---- */
V.search = (r) => {
  const q = r.slice(1).join("/");
  const n = norm(q);
  const hit = (s) => n && norm(s).includes(n);
  const G = [];
  const add = (t, items) => {
    if (items.length) G.push([t, items]);
  };
  add(
    "Объекты",
    S.projects
      .filter((p) => hit(p.name + " " + p.cipher + " " + p.address))
      .map((p) => [`#/p/${p.id}`, p.name, p.address]),
  );
  add(
    "Системы",
    S.projects.flatMap((p) =>
      p.systems
        .filter((s) => hit(s.code + " " + s.name + " " + s.cipher))
        .map((s) => [`#/s/${s.id}`, s.code + " — " + s.name, p.name]),
    ),
  );
  add(
    "Акты",
    S.projects.flatMap((p) =>
      p.systems.flatMap((s) =>
        s.acts
          .filter((a) =>
            hit(a.num + " " + a.works + " " + a.place + " " + a.rd),
          )
          .map((a) => [
            `#/a/${a.id}`,
            a.num + " · " + a.works,
            p.name + " · " + s.code,
          ]),
      ),
    ),
  );
  add(
    "АИК",
    S.projects.flatMap((p) =>
      p.systems.flatMap((s) =>
        s.aik
          .filter((k) => hit(k.num + " " + mName(pMat(p, k.materialId))))
          .map((k) => [
            `#/k/${k.id}`,
            k.num + " · " + mName(pMat(p, k.materialId)),
            p.name + " · " + s.code,
          ]),
      ),
    ),
  );
  add(
    "Материалы объектов",
    S.projects.flatMap((p) =>
      p.materials
        .filter((m) =>
          hit(
            mName(m) +
              " " +
              mF(m, "maker") +
              " " +
              mDocs(m)
                .map((d) => d.num)
                .join(" "),
          ),
        )
        .map((m) => [`#/m/${m.id}`, mName(m), p.name]),
    ),
  );
  add(
    "База паспортов",
    S.lib.base
      .filter((b) =>
        hit(b.name + " " + b.maker + " " + b.docs.map((d) => d.num).join(" ")),
      )
      .map((b) => [
        `#/lib/base/${b.id}`,
        b.name,
        b.docs.map((d) => d.num).join(", "),
      ]),
  );
  add("Организации и представители", [
    ...S.lib.orgs
      .filter((o) => hit(o.full + " " + o.short + " " + o.inn))
      .map((o) => [`#/lib/orgs/${o.id}`, o.short, o.role]),
    ...S.lib.people
      .filter((x) => hit(x.fio + " " + x.position))
      .map((x) => [`#/lib/people/${x.id}`, x.fioShort, x.position]),
  ]);
  const tot = G.reduce((s, g) => s + g[1].length, 0);
  return `<div class="page">${hdr("Поиск", q ? `«${esc(q)}» — найдено ${tot}` : "Введите запрос в строке поиска")}${
    G.map(
      ([t, items]) =>
        `<div class="card" style="padding:0"><h3 style="padding:14px 16px 4px">${esc(t)} <span class="pill p-n">${items.length}</span></h3>${items
          .slice(0, 30)
          .map(
            ([h, a, b]) =>
              `<div class="msg" data-a="nav" data-h="${h}"><span class="grow">${esc(a)}</span><span class="small mut">${esc(b || "")}</span></div>`,
          )
          .join("")}</div>`,
    ).join("") || (q ? '<div class="empty">Ничего не найдено</div>' : "")
  }</div>`;
};
