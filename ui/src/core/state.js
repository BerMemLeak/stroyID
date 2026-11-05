/* ---------- хранение: база = папка на Яндекс Диске (в прототипе — имитация) ---------- */
const LSA = "stroiid_full_app_v4",
  LSP = "stroiid_full_base_v4|",
  LSB = "stroiid_full_bk_v4|";
const DEMO_PATH = "СтройИД — локальная база";
let APP;
try {
  APP = JSON.parse(localStorage.getItem(LSA));
} catch (e) {
  APP = null;
}
if (!APP || APP.v !== 30)
  APP = {
    v: 30,
    user: "",
    pc: "PTO-01",
    current: "",
    trashDays: 30,
    recent: [
      {
        path: DEMO_PATH,
        name: "СтройИД — ООО «СтройМонтаж»",
        last: "01.10.2026, 09:12",
      },
      {
        path: "D:\\YandexDisk\\СтройИД_Архив_2025",
        name: "Архив 2025",
        last: "14.01.2026, 16:40",
      },
    ],
  };
function saveApp(app = APP) {
  try {
    localStorage.setItem(LSA, JSON.stringify(app));
  } catch (e) {}
}
let S = null,
  IX = null;
function loadBase(path) {
  try {
    const d = JSON.parse(localStorage.getItem(LSP + path));
    return d && d.meta && d.meta.v === 30 ? d : null;
  } catch (e) {
    return null;
  }
}
function openBase(path) {
  let d = loadBase(path);
  if (!d && path === DEMO_PATH) d = seed();
  if (!d) return false;
  S = d;
  IX = null;
  S.locks = S.locks || {};
  S.builds = S.builds || [];
  S.ui.user = APP.user;
  APP.current = path;
  Object.values(S.locks).forEach((L) =>
    L.forEach((l) => {
      if (l.demo === "fresh") l.pulse = iso();
    }),
  );
  let r = APP.recent.find((x) => x.path === path);
  if (!r) {
    r = { path };
    APP.recent.unshift(r);
  }
  r.name = S.meta.name;
  r.last = nowStr();
  APP.recent = [r, ...APP.recent.filter((x) => x !== r)].slice(0, 8);
  saveApp();
  autoClean();
  logH("Открыта база на компьютере " + APP.pc);
  save();
  return true;
}
function closeBase() {
  if (!S) return;
  releaseMine(null);
  save();
  S = null;
  IX = null;
  APP.current = "";
  saveApp();
}
function save() {
  IX = null;
  if (!S) return;
  S.ui.saved = nowStr();
  S.ui.user = APP.user;
  try {
    localStorage.setItem(LSP + APP.current, JSON.stringify(S));
  } catch (e) {
    toast("Не удалось сохранить: недостаточно места");
  }
}

function dataOnly() {
  const d = clone(S);
  delete d.locks;
  d.projects.forEach((p) => {
    if (p.logo) p.logo = "[файл]";
    p.systems.forEach((s) =>
      s.acts.forEach((a) =>
        a.photos.forEach((ph) => {
          if (ph.img) ph.img = "[файл]";
        }),
      ),
    );
  });
  d.lib.people.forEach((x) => {
    if (x.sign) x.sign = "[файл]";
  });
  return d;
}

function autoClean() {
  const lim = (+APP.trashDays || 30) * 864e5;
  const n = S.trash.length;
  S.trash = S.trash.filter(
    (t) => !t.iso || Date.now() - Date.parse(t.iso) < lim,
  );
  if (S.trash.length < n)
    logH("Корзина: автоматически удалено " + (n - S.trash.length));
}
function logH() {}
