/* ===================== СЛУЖЕБНОЕ ===================== */
function toast(m) {
  const d = document.createElement("div");
  d.textContent = m;
  $("#toast").appendChild(d);
  setTimeout(() => d.remove(), 3600);
}
let MB = [];
function modal(title, body, btns = [{ l: "Закрыть" }], cls = "") {
  MB = btns;
  $("#modal-root").innerHTML =
    `<div class="ov"><div class="dlg ${cls}" role="dialog" aria-label="${esc(title)}"><div class="dh">${esc(title)}<button class="x" data-mb="-1" aria-label="Закрыть">×</button></div><div class="db">${body}</div><div class="df">${btns.map((b, i) => `<button class="btn ${b.c || ""}" data-mb="${i}">${esc(b.l)}</button>`).join("")}</div></div></div>`;
  const f = $("#modal-root input:not([type=checkbox]),#modal-root select");
  if (f) f.focus();
}
function closeModal() {
  $("#modal-root").innerHTML = "";
  MB = [];
}
function confirmBox(title, text, ok, okL = "Удалить") {
  modal(title, `<div>${text}</div>`, [
    { l: "Отмена" },
    { l: okL, c: "pri", f: ok },
  ]);
}
function closeMenu() {
  const m = $("#mimenu");
  if (m) m.remove();
}
function pickFiles(accept, multiple) {
  return new Promise((res) => {
    const i = document.createElement("input");
    i.type = "file";
    i.accept = accept || "";
    i.multiple = !!multiple;
    i.onchange = () => res([...i.files]);
    i.click();
  });
}
async function pdfPages(file) {
  try {
    if (!/\.pdf$/i.test(file.name)) return 1;
    const t = new TextDecoder("latin1").decode(await file.arrayBuffer());
    const m = t.match(/\/Type\s*\/Page(?!s)/g);
    return m ? m.length : 1;
  } catch (e) {
    return 1;
  }
}
function imgToData(file, max = 640) {
  return new Promise((res) => {
    const fr = new FileReader();
    fr.onload = () => {
      const im = new Image();
      im.onload = () => {
        const k = Math.min(1, max / Math.max(im.width, im.height));
        const c = document.createElement("canvas");
        c.width = im.width * k;
        c.height = im.height * k;
        c.getContext("2d").drawImage(im, 0, 0, c.width, c.height);
        res(c.toDataURL("image/jpeg", 0.72));
      };
      im.onerror = () => res("");
      im.src = fr.result;
    };
    fr.readAsDataURL(file);
  });
}
async function zipRead(file, re) {
  const buf = new Uint8Array(await file.arrayBuffer());
  const dv = new DataView(buf.buffer);
  let e = -1;
  for (let i = buf.length - 22; i >= 0; i--) {
    if (dv.getUint32(i, true) === 0x06054b50) {
      e = i;
      break;
    }
  }
  if (e < 0) return {};
  const n = dv.getUint16(e + 10, true);
  let p = dv.getUint32(e + 16, true);
  const out = {};
  for (let k = 0; k < n; k++) {
    const meth = dv.getUint16(p + 10, true),
      cs = dv.getUint32(p + 20, true),
      nl = dv.getUint16(p + 28, true),
      xl = dv.getUint16(p + 30, true),
      cl = dv.getUint16(p + 32, true),
      lo = dv.getUint32(p + 42, true);
    const name = new TextDecoder().decode(buf.slice(p + 46, p + 46 + nl));
    p += 46 + nl + xl + cl;
    if (!re.test(name)) continue;
    const ln = dv.getUint16(lo + 26, true),
      lx = dv.getUint16(lo + 28, true);
    const data = buf.slice(lo + 30 + ln + lx, lo + 30 + ln + lx + cs);
    if (meth === 0) out[name] = new TextDecoder().decode(data);
    else {
      const ds = new Blob([data])
        .stream()
        .pipeThrough(new DecompressionStream("deflate-raw"));
      out[name] = await new Response(ds).text();
    }
  }
  return out;
}
async function docxTags(file) {
  try {
    const z = await zipRead(
      file,
      /^word\/(document|header\d*|footer\d*)\.xml$/,
    );
    const tags = new Set();
    Object.values(z).forEach((xml) => {
      const txt = xml.replace(/<[^>]+>/g, "");
      (txt.match(/\{\{\s*([^{}]+?)\s*\}\}/g) || []).forEach((m) =>
        tags.add(m.replace(/[{}\s]/g, "")),
      );
    });
    return [...tags];
  } catch (e) {
    console.warn(e);
    return [];
  }
}
function download(name, content, type) {
  const b = new Blob([content], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(b);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 500);
}
function csv(rows) {
  return (
    "\ufeff" +
    rows
      .map((r) =>
        r
          .map((v) => {
            v = String(v ?? "");
            return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
          })
          .join(";"),
      )
      .join("\r\n")
  );
}
function touch(o) {
  if (o && typeof o === "object" && o !== S && o !== S.ui && o !== APP) {
    o.updated = nowStr();
    o.updatedBy = APP.user;
  }
}
function commit(msg, o) {
  if (o) touch(o);
  if (msg) logH(msg);
  save();
  render();
}
function guard(key) {
  if (S.ui.ro) {
    toast("Включён режим только просмотра — изменения запрещены");
    return false;
  }
  if (key === undefined) key = routeKey();
  if (!key) return true;
  const L = lockInfo(key);
  if (L.blockedBy) {
    toast(`Только просмотр: ${lockName(key)} редактирует ${L.blockedBy.user}`);
    return false;
  }
  if (L.stale.length && !L.mine) {
    A.lockStale({ k: key });
    return false;
  }
  takeLock(key);
  return true;
}
function container(ent, c) {
  if (LIBK[ent]) return S.lib[LIBK[ent]];
  if (ent === "proj") return S.projects;
  if (ent === "sys") return c.p?.systems;
  if (ent === "act") return c.s?.acts;
  if (ent === "aik") return c.s?.aik;
  if (ent === "jr") return (c.s || c.p)?.journals;
  if (ent === "mat") return c.p?.materials;
}
function toTrash(ent, id) {
  const c = ctx(ent, id);
  const arr = container(ent, c);
  if (!arr) return;
  const i = arr.findIndex((x) => x.id === id);
  if (i < 0) return;
  const item = arr.splice(i, 1)[0];
  S.trash.unshift({
    id: uid(),
    ent,
    item,
    ctx: { pid: c.p?.id || "", sid: c.s?.id || "" },
    ts: nowStr(),
    iso: iso(),
    by: APP.user,
  });
  logH("Удалён(а) " + entLabel(ent, item) + " (в корзину)");
  IX = null;
}
const ROWT = {
  doc: () => ({
    id: uid(),
    type: "Сертификат соответствия",
    num: "",
    date: "",
    file: "",
    pages: 0,
  }),
  scheme: (a) => ({
    id: uid(),
    name: "Исполнительная схема",
    file: "",
    pages: 0,
    format: "A3",
    orient: "Альбомная",
    rd: a.rd || "",
    tol: "в пределах допусков",
    pos: "Правый верхний угол",
    mx: 70,
    my: 5,
    stamped: false,
  }),
  test: (a) => ({
    id: uid(),
    name: "",
    num: "",
    date: a.end || today(),
    file: "",
    pages: 0,
  }),
  remark: () => ({ id: uid(), text: "", date: today(), done: false }),
  extra: () => ({ id: uid(), k: "Новый реквизит", v: "" }),
};

/* ---------- ввод данных ---------- */
function apply(t, fromInput) {
  const ent = t.dataset.ent,
    id = t.dataset.id,
    f = t.dataset.f;
  if (!["ui", "root", "app"].includes(ent) && !guard(entKey(ent, id))) {
    render();
    return;
  }
  const o = getEnt(ent, id);
  if (!o) return;
  let v = t.type === "checkbox" ? t.checked : t.value;
  if (t.type === "number") v = v === "" ? "" : Number(v);
  if (f === "docRole" || f === "photoLayout") v = Number(v);
  if (["start", "end", "validFrom", "validTo"].includes(f)) {
    const a = f === "start" || f === "validFrom" ? v : o.start || o.validFrom,
      b = f === "end" || f === "validTo" ? v : o.end || o.validTo;
    if (a && b && b < a) {
      toast("Окончание не может быть раньше начала");
      t.value = getPath(o, f) || "";
      return;
    }
  }
  const old = getPath(o, f);
  if (old === v) {
    if (!fromInput && t.dataset.rr) render();
    return;
  }
  if (ent === "app" && (f === "user" || f === "pc")) releaseMine(null);
  setPath(o, f, v);
  if (ent === "per" && f === "fio") o.fioShort = shortFio(v);
  if (ent === "app" && !window.manualSavingMode) saveApp();
  if (ent === "root" && f === "meta.name") {
    const rc = APP.recent.find((x) => x.path === APP.current);
    if (rc) {
      rc.name = v;
      saveApp();
    }
  }
  if (ent === "act" && f === "type") {
    const s = ctx("act", id).s;
    o.num = nextNum(s, v, o.id);
  }
  if (ent === "aik" && f === "materialId") {
    const s = ctx("aik", id).s;
    s.acts.forEach((a) =>
      Object.keys(a.aikLinks).forEach((m) => {
        if (a.aikLinks[m] === o.id && m !== v) delete a.aikLinks[m];
      }),
    );
  }
  if (!["ui", "root", "app"].includes(ent)) {
    touch(o);
    logH("Изменён(а) " + entLabel(ent, o));
  }
  save({ field: true });
  if (t.dataset.rr && !fromInput) render();
  else refreshChrome();
}
const isTextual = (t) =>
  t.tagName === "TEXTAREA" ||
  (t.tagName === "INPUT" &&
    !["checkbox", "radio", "date", "file", "number"].includes(t.type));
document.addEventListener("input", (e) => {
  const t = e.target;
  if (!t.dataset || !t.dataset.f) return;
  if (isTextual(t)) apply(t, true);
});
// Native date editors emit change for partial years (e.g. 0002). Commit only
// after leaving the field, without rebuilding the DOM under the next click.
function applyDate(t) {
  if (t.validity.badInput) {
    t.value = getPath(getEnt(t.dataset.ent, t.dataset.id), t.dataset.f) || "";
    toast("Введите дату полностью");
    return;
  }
  apply(t, true);
}
document.addEventListener("change", (e) => {
  const t = e.target;
  if (!t.dataset || !t.dataset.f) return;
  if (t.type === "date") {
    if (document.activeElement !== t) applyDate(t);
    return;
  }
  if (isTextual(t)) {
    fsRename(t);
    if (t.dataset.rr && !window.manualSavingMode) render();
    return;
  }
  apply(t, false);
});
document.addEventListener("focusout", (e) => {
  const t = e.target;
  if (t.type === "date" && t.dataset?.f) applyDate(t);
});
function fsRename(t) {
  if (t.dataset.orig === undefined) return;
  const k = t.dataset.fsk;
  const o = getEnt(t.dataset.ent, t.dataset.id);
  if (!o) return;
  const nv = fsName(t.value, k === "act" ? 30 : k === "sys" ? 20 : 40);
  if (nv === t.dataset.orig) {
    o.dir = nv;
    return;
  }
  const c = ctx(t.dataset.ent, t.dataset.id);
  const sib =
    k === "act"
      ? c.s?.acts.filter((x) => x.id !== o.id).map(actDir)
      : k === "sys"
        ? c.p?.systems.filter((x) => x.id !== o.id).map(sysDir)
        : S.projects.filter((x) => x.id !== o.id).map(objDir);
  if (sib && sib.includes(nv)) {
    o.dir = t.dataset.orig;
    save();
    toast(
      `Папка «${nv}» уже есть — папка остаётся «${t.dataset.orig}», пока имя не станет уникальным`,
    );
    return;
  }
  o.dir = nv;
  save();
  toast(`Папка переименована: ${t.dataset.orig} → ${nv}`);
  t.dataset.orig = nv;
}
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") {
    e.preventDefault();
    $("#gsearch")?.focus();
  }
  if (e.key === "Escape") {
    closeModal();
    closeMenu();
  }
  if (e.key === "Enter" && e.target.id === "gsearch") A.doSearch();
  if (e.key === "Enter" && e.target.dataset?.rr && e.target.tagName === "INPUT")
    e.target.blur();
});
document.addEventListener("click", (e) => {
  const mb = e.target.closest("[data-mb]");
  if (mb) {
    const b = MB[+mb.dataset.mb];
    if (b && b.f) {
      const currentButtons = MB;
      if (b.f() === false || MB !== currentButtons) return;
    }
    closeModal();
    return;
  }
  if (e.target.classList.contains("ov")) {
    closeModal();
    return;
  }
  if (!e.target.closest("#mimenu")) closeMenu();
  const el = e.target.closest("[data-a]");
  if (!el) return;
  const a = el.dataset.a;
  if (el.tagName !== "INPUT") e.preventDefault();
  if (a !== "menu") closeMenu();
  if (!A[a]) {
    toast("Действие — заглушка прототипа");
    return;
  }
  A[a](el.dataset, el, e);
});
