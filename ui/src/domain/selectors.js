/* ---------- индекс и доступ к данным ---------- */
function ix() {
  if (IX) return IX;
  const X = { proj: {}, sys: {}, act: {}, aik: {}, jr: {}, mat: {} };
  S.projects.forEach((p) => {
    X.proj[p.id] = { o: p };
    p.materials.forEach((m) => (X.mat[m.id] = { o: m, p }));
    p.journals.forEach((j) => (X.jr[j.id] = { o: j, p }));
    p.systems.forEach((s) => {
      X.sys[s.id] = { o: s, p };
      s.acts.forEach((a) => (X.act[a.id] = { o: a, p, s }));
      s.aik.forEach((k) => (X.aik[k.id] = { o: k, p, s }));
      s.journals.forEach((j) => (X.jr[j.id] = { o: j, p, s }));
    });
  });
  return (IX = X);
}
const LIBK = {
  base: "base",
  org: "orgs",
  per: "people",
  ord: "orders",
  pf: "profiles",
  tpl: "templates",
};
function getEnt(ent, id) {
  if (ent === "app") return APP;
  if (ent === "ui") return S.ui;
  if (ent === "root") return S;
  if (LIBK[ent]) return S.lib[LIBK[ent]].find((x) => x.id === id);
  const e = ix()[ent]?.[id];
  return e ? e.o : null;
}
const ctx = (ent, id) => ix()[ent]?.[id] || {};
const proj = (id) => getEnt("proj", id);
const person = (id) => S.lib.people.find((x) => x.id === id);
const org = (id) => S.lib.orgs.find((x) => x.id === id);
const prof = (id) => S.lib.profiles.find((x) => x.id === id);
const tpl = (id) => S.lib.templates.find((x) => x.id === id);
function baseOf(m) {
  return m && m.baseId
    ? S.lib.base.find((b) => b.id === m.baseId) ||
        S.trash.find((t) => t.ent === "base" && t.item.id === m.baseId)?.item
    : null;
}
const mName = (m) => (m ? baseOf(m)?.name || m.name : "");
function mDocs(m) {
  if (!m) return [];
  if (!m.baseId) return m.docs || [];
  const b = baseOf(m);
  return [
    ...(b?.docs || []),
    ...S.trash
      .filter(
        (t) =>
          t.ent === "row" &&
          t.ctx?.parentEnt === "base" &&
          t.ctx.parentId === m.baseId &&
          t.ctx.path === "docs",
      )
      .map((t) => t.item),
  ];
}
const mF = (m, f) => (m ? (m.baseId ? baseOf(m)?.[f] || "" : m[f]) : "");
let pMat = (p, id) => p.materials.find((x) => x.id === id);
const spOf = (s, id) => s.subprofiles.find((x) => x.id === id);
const sortedSys = (p) => p.systems.slice().sort((a, b) => a.order - b.order);
const sortActs = (l) =>
  l
    .slice()
    .sort(
      (a, b) =>
        (a.type === b.type ? 0 : a.type === "АОСР" ? -1 : 1) ||
        String(a.num).localeCompare(String(b.num), "ru", { numeric: true }),
    );
const signer = (a, sp, i) =>
  a.signers?.["r" + i] || sp?.signers?.["r" + i] || "";
function nextNum(s, type, exceptId) {
  const coll = type === "АИК" ? s.aik : s.acts.filter((a) => a.type === type);
  let mx = 0;
  coll.forEach((a) => {
    if (a.id === exceptId) return;
    const m = String(a.num).match(/(\d+)\s*$/);
    if (m) mx = Math.max(mx, +m[1]);
  });
  return type + "-" + pad(mx + 1);
}
function photoSheets(a) {
  return a.photos.length
    ? Math.ceil(a.photos.length / (+a.photoLayout || 2))
    : 0;
}
function appsText(a, s) {
  const p = [];
  if (s?.scheme?.file)
    p.push(
      `Исполнительная схема системы ${s.code} на ${s.scheme.pages || "?"} л.`,
    );
  a.schemes.forEach((x) => p.push(`${x.name} на ${x.pages || "?"} л.`));
  a.tests.forEach((t) =>
    p.push(`${t.name}${t.num ? " № " + t.num : ""} на ${t.pages || "?"} л.`),
  );
  const ph = photoSheets(a);
  if (ph) p.push(`Фототаблица на ${ph} л.`);
  return p.join("; ") || "—";
}
function norm(s) {
  return String(s)
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^a-zа-я0-9]+/g, " ")
    .trim();
}
function similar(a, b) {
  const A = new Set(
      norm(a)
        .split(" ")
        .filter((x) => x.length > 1),
    ),
    B = new Set(
      norm(b)
        .split(" ")
        .filter((x) => x.length > 1),
    );
  if (!A.size || !B.size) return false;
  let i = 0;
  A.forEach((x) => {
    if (B.has(x)) i++;
  });
  return i / Math.min(A.size, B.size) >= 0.75;
}
function setPath(o, path, v) {
  const ps = path.split(".");
  let cur = o;
  for (let i = 0; i < ps.length - 1; i++) {
    const k = ps[i];
    cur = k[0] === "#" ? cur.find((x) => x.id === k.slice(1)) : cur[k];
    if (cur == null) return;
  }
  cur[ps[ps.length - 1]] = v;
}
function getPath(o, path) {
  return path
    .split(".")
    .reduce(
      (c, k) =>
        c == null
          ? c
          : k[0] === "#"
            ? c.find((x) => x.id === k.slice(1))
            : c[k],
      o,
    );
}
const ENT_NAME = {
  proj: "объект",
  sys: "система",
  act: "акт",
  aik: "АИК",
  jr: "журнал",
  mat: "материал",
  base: "паспорт из базы",
  org: "организация",
  per: "представитель",
  ord: "приказ",
  pf: "профиль заказчика",
  tpl: "шаблон",
};
function entLabel(ent, o) {
  if (!o) return "";
  if (ent === "proj") return ENT_NAME.proj + " «" + (o.name || "") + "»";
  return (
    (ENT_NAME[ent] || ent) +
    " «" +
    (o.num || o.short || o.code || o.fioShort || mName(o) || o.name || "") +
    "»"
  );
}
function slug(s) {
  return String(s)
    .replace(/[«»"]/g, "")
    .replace(/[\\/:*?<>|]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 48);
}
const TAGS = [];
