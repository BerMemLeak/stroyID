/* ---------- маршрутизация ---------- */
function route() {
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
  const p = h.split("/").filter(Boolean);
  return p.length ? p : ["home"];
}
function go(h) {
  if (location.hash === h) render();
  else location.hash = h;
}
window.addEventListener("hashchange", render);
function curProject() {
  const r = route();
  const k = r[0],
    id = r[1];
  if (k === "p") return proj(id);
  if (["s", "a", "k", "j", "m"].includes(k)) {
    const map = { s: "sys", a: "act", k: "aik", j: "jr", m: "mat" };
    return ctx(map[k], id).p;
  }
  if (k === "build") return proj(id || S.ui.build.pid);
  return null;
}

/* ---------- дерево слева ---------- */
function renderTree() {
  const r = route();
  const k = r[0],
    id = r[1];
  const X = ix();
  let curSys = null,
    curAct = null,
    curProj = null;
  if (k === "p") curProj = id;
  if (k === "s") curSys = id;
  if (k === "a") {
    curAct = id;
    curSys = X.act[id]?.s?.id;
  }
  if (k === "k") curSys = X.aik[id]?.s?.id;
  if (k === "j") {
    curSys = X.jr[id]?.s?.id;
    if (!curSys) curProj = X.jr[id]?.p?.id;
  }
  if (k === "m") curProj = X.mat[id]?.p?.id;
  const ex = (x) => !!S.ui.exp[x];
  const tw = (key, has) =>
    has
      ? `<span class="tg${ex(key) ? " o" : ""}" data-a="tw" data-k="${key}">${ic("chev", "")}</span>`
      : '<span class="tg"></span>';
  let h = `<div class="sh">Объекты<button data-a="newProject" title="Новый объект">+</button></div>`;
  S.projects.forEach((p) => {
    const C = check(p);
    const on = curProj === p.id && k === "p";
    h += `<div class="tn${on ? " on" : ""}">${tw(p.id, 1)}<a href="#/p/${p.id}" title="${esc(p.name)}">${ic("bld")}<span class="lb">${esc(p.name)}</span>${lockMark("obj:" + p.id)}${C.E.length ? `<span class="warn err" title="Ошибок: ${C.E.length}">!</span>` : ""}</a></div>`;
    if (ex(p.id)) {
      sortedSys(p).forEach((s) => {
        const on = curSys === s.id && !curAct;
        const done = s.acts.filter((a) => a.status === "Готово").length;
        h += `<div class="tn${on ? " on" : ""}" style="padding-left:18px">${tw(s.id, 1)}<a href="#/s/${s.id}" title="${esc(s.code + " — " + s.name)}">${ic("sys")}<span class="lb"><b style="font-weight:600">${esc(s.code)}</b> <span class="mut">${esc(s.name)}</span></span>${lockMark("sys:" + s.id)}${!s.scheme.file ? '<span class="warn" title="Нет исполнительной схемы системы">!</span>' : ""}<span class="ct">${done}/${s.acts.length}</span></a></div>`;
        if (ex(s.id)) {
          sortActs(s.acts).forEach((a) => {
            h += `<div class="tn${curAct === a.id ? " on" : ""}" style="padding-left:38px"><span class="tg"></span><a href="#/a/${a.id}" title="${esc(a.num + " — " + a.works)}"><i class="dot ${a.status === "Готово" ? "g" : "a"}"></i><span class="lb">${esc(a.num)} <span class="mut">${esc(a.works)}</span></span></a></div>`;
          });
          h += `<div class="tn add" style="padding-left:38px"><span class="tg"></span><a href="#" data-a="newAct" data-s="${s.id}">${ic("plus")}<span class="lb">Новый АОСР</span></a></div>`;
        }
      });
      h += `<div class="tn add" style="padding-left:18px"><span class="tg"></span><a href="#" data-a="newSystem" data-p="${p.id}">${ic("plus")}<span class="lb">Добавить систему</span></a></div>`;
    }
  });
  const nav = (href, label, icon, match) =>
    `<div class="tn${match ? " on" : ""}"><span class="tg"></span><a href="${href}">${ic(icon)}<span class="lb">${label}</span></a></div>`;
  h +=
    `<div class="sh">Справочники${S.locks.lib ? lockMark("lib") : ""}</div>` +
    nav(
      "#/lib/orgs",
      "Организации и подписанты",
      "users",
      k === "lib" && id === "orgs",
    ) +
    nav("#/lib/base", "База паспортов", "box", k === "lib" && id === "base") +
    nav(
      "#/lib/profiles",
      "Профили и шаблоны",
      "tag",
      k === "lib" && ["profiles", "templates", "tags"].includes(id),
    );
  h +=
    `<div class="sh">Инструменты</div>` +
    nav("#/build", "Сборка тома", "layers", k === "build") +
    nav("#/import", "Импорт", "imp", k === "import") +
    nav("#/files", "Папка базы", "folder", k === "files") +
    nav("#/settings", "Настройки", "gear", k === "settings");
  $("#tree").innerHTML = h;
  $("#sidefoot").innerHTML = `<div class="ava">${esc(
    APP.user
      .split(" ")
      .map((x) => x[0])
      .slice(0, 2)
      .join(""),
  )}</div><div class="grow" style="min-width:0"><div style="color:var(--tx);font-weight:550;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(S.meta.name)}">${esc(S.meta.name)}</div><div>${esc(APP.user)} · ${esc(APP.pc)}${S.ui.ro ? " · просмотр" : ""}</div></div>${B(ic("sync"), "baseSwitch", 'title="Сменить базу" aria-label="Сменить базу"', "sm icon ghost")}`;
}
function renderTop() {
  const p = curProject();
  let pill = "";
  if (p) {
    const C = check(p);
    pill = `<a class="checkpill" href="#/p/${p.id}/check" title="Проверка комплектности объекта">${C.E.length ? `<i class="dot" style="background:var(--red)"></i><b>${C.E.length}</b> ошиб.` : ""}${C.W.length ? `<i class="dot a"></i><b>${C.W.length}</b> предупр.` : ""}${!C.E.length && !C.W.length ? '<i class="dot g"></i>Комплект в порядке' : ""}</a>`;
  }
  $("#top").innerHTML =
    `<div class="search">${ic("search", "")}<input id="gsearch" type="text" placeholder="Поиск: № акта, работы, материал, № сертификата, система" value="${esc(S.ui.q || "")}"></div><div class="sp"></div>${pill}${B(ic("layers") + "Сборка тома", "nav", `data-h="#/build${p ? "/" + p.id : ""}"`, "pri")}${B(ic("more"), "menu", 'title="Меню" aria-label="Меню"', "icon")}`;
}
function refreshChrome() {
  renderTree();
  renderTop();
  renderStatus();
}

/* ---------- отрисовка ---------- */
const V = {};
function render() {
  closeMenu();
  const app = $("#app");
  if (!APP.user || !S) {
    app.classList.add("bare");
    $("#content").innerHTML = !APP.user ? V.welcome() : V.start();
    return;
  }
  app.classList.remove("bare");
  const r = route();
  const key = routeKey();
  if (releaseMine(key)) save();
  const fn = V[r[0]] || V.home;
  let html;
  try {
    html = fn(r);
  } catch (e) {
    console.error(e);
    html = `<div class="page">${hdr("Ошибка отображения", "")}<div class="alert al-r">${esc(e.message)}</div></div>`;
  }
  const L = key && S.locks[key] ? lockInfo(key) : null;
  $("#content").innerHTML =
    (S.ui.ro
      ? `<div class="ro-banner row"><span class="grow">Режим только просмотра — изменения запрещены.</span>${B("Включить редактирование", "roToggle", "", "sm")}</div>`
      : lockBar(key)) + html;
  if (S.ui.ro || (L && (L.blockedBy || (L.stale.length && !L.mine))))
    document
      .querySelectorAll(
        "#content input[data-f],#content select[data-f],#content textarea[data-f],#content input[data-a]",
      )
      .forEach((x) => {
        if (!["ui", "root", "app"].includes(x.dataset.ent)) x.disabled = true;
      });
  refreshChrome();
}
