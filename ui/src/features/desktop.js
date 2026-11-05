/* Per-card folder persistence. */
let desktop,
  desktopRevision = 0,
  desktopPending = null,
  desktopSaving = null,
  desktopTimer,
  desktopError = "",
  desktopJobs = new Set(),
  folderWarnings = [],
  folderConflicts = [],
  folderPolling = false,
  desktopClosing = false;
const desktopAsyncOps = new Set([
  "load",
  "save",
  "poll",
  "repairCard",
  "cardData",
  "trashMove",
  "trashRestore",
  "trashPurge",
  "recoverMissing",
  "sampleDocx",
  "referenceTemplate",
]);
let desktopRequestId = 0;
const desktopReplies = new Map();
function nativeCall(op, params = {}) {
  return new Promise((resolve, reject) => {
    const receive = (raw) => {
      try {
        const r = JSON.parse(raw);
        if (!r.ok) {
          const error = Error(r.error);
          error.details = r.details || [];
          throw error;
        }
        resolve(r.value);
      } catch (e) {
        reject(e);
      }
    };
    if (desktop.requestAsync && desktopAsyncOps.has(op)) {
      const id = String(++desktopRequestId);
      desktopReplies.set(id, receive);
      desktop.requestAsync(id, op, JSON.stringify(params));
    } else desktop.request(op, JSON.stringify(params), receive);
  });
}
function desktopTrack(p) {
  desktopJobs.add(p);
  p.finally(() => desktopJobs.delete(p)).catch(() => {});
  return p;
}
function emptyDesktop() {
  const d = seed();
  d.meta.name = "СтройИД — рабочая база";
  d.projects = [];
  for (const k of ["orgs", "people", "orders", "base", "templates", "profiles"])
    d.lib[k] = [];
  d.history = [];
  d.trash = [];
  d.builds = [];
  d.volCfg = {};
  d.locks = {};
  d.ui.exp = {};
  d.ui.ro = false;
  return d;
}
function rebase(base, local, remote) {
  if (JSON.stringify(local) === JSON.stringify(base)) return remote;
  if (
    Array.isArray(local) &&
    Array.isArray(base) &&
    Array.isArray(remote) &&
    [...local, ...base, ...remote].every(
      (x) => x && typeof x === "object" && x.id,
    )
  ) {
    const b = new Map(base.map((x) => [x.id, x])),
      l = new Map(local.map((x) => [x.id, x])),
      r = new Map(remote.map((x) => [x.id, x]));
    return [...new Set([...r.keys(), ...l.keys()])]
      .filter((id) => !(b.has(id) && !l.has(id)))
      .map((id) =>
        l.has(id) ? rebase(b.get(id), l.get(id), r.get(id)) : r.get(id),
      )
      .filter(Boolean);
  }
  if (
    local &&
    base &&
    remote &&
    !Array.isArray(local) &&
    typeof local === "object" &&
    typeof base === "object" &&
    typeof remote === "object"
  ) {
    const out = { ...remote };
    for (const k of new Set([...Object.keys(base), ...Object.keys(local)])) {
      if (!(k in local)) delete out[k];
      else out[k] = rebase(base[k], local[k], remote[k]);
    }
    return out;
  }
  return local;
}
function reconcile(target, value) {
  if (Array.isArray(target) && Array.isArray(value)) {
    const prior = target.slice(),
      map = new Map(
        prior
          .filter((x) => x && typeof x === "object" && x.id)
          .map((x) => [x.id, x]),
      );
    const next = value.map((v, i) => {
      if (v && typeof v === "object" && v.id)
        return map.has(v.id) ? reconcile(map.get(v.id), v) : structuredClone(v);
      const old = prior[i];
      return v &&
        typeof v === "object" &&
        old &&
        typeof old === "object" &&
        !old.id
        ? reconcile(old, v)
        : structuredClone(v);
    });
    target.splice(0, target.length, ...next);
    return target;
  }
  if (
    target &&
    value &&
    typeof target === "object" &&
    typeof value === "object" &&
    !Array.isArray(target) &&
    !Array.isArray(value)
  ) {
    if (target === value) return target;
    for (const k of Object.keys(target)) if (!(k in value)) delete target[k];
    for (const [k, v] of Object.entries(value))
      target[k] = reconcile(target[k], v);
    return target;
  }
  return value;
}
function ensureDesktopUi(prefs = S?.ui) {
  const defaults = desktopUiDefaults || {};
  S.ui = {
    ...structuredClone(defaults),
    ...(S.ui || {}),
    ...structuredClone(prefs || {}),
  };
  for (const k of ["exp", "sel", "f", "build"])
    if (!S.ui[k] || typeof S.ui[k] !== "object" || Array.isArray(S.ui[k]))
      S.ui[k] = structuredClone(defaults[k] || {});
}

function acceptFolder(r, sent = null) {
  if (
    !r.preview &&
    r.root === APP.current &&
    Number.isFinite(r.revision) &&
    r.revision < desktopRevision
  )
    return false;
  desktopRevision = r.revision;
  folderWarnings = r.warnings || [];
  folderConflicts = r.conflicts || [];
  if (r.state) {
    const prefs = structuredClone(S?.ui || {});
    if (!r.preview) {
      desktopSavedState = JSON.parse(JSON.stringify(r.state));
      desktopSavedHeads = r.editHeads || desktopSavedHeads;
    }
    S = reconcile(S, sent ? rebase(sent, S, r.state) : r.state);
    ensureDesktopUi(prefs);
    S.locks = {};
    IX = null;
    ensureWorkspace();
  }
  APP.current = r.root || APP.current;
}
let desktopDirty = false,
  desktopEditVersion = 0,
  desktopSavedState = null,
  desktopSavedHeads = null,
  desktopUiDefaults = null,
  desktopRemoteWaiting = false;
async function desktopPollFolder() {
  const version = desktopEditVersion,
    before = JSON.stringify(S),
    r = await nativeCall("poll");
  if (desktopClosing) return false;
  if (desktopDirty || version !== desktopEditVersion) {
    desktopRemoteWaiting = true;
    renderStatus();
    return false;
  }
  acceptFolder(r);
  return before !== JSON.stringify(S);
}
save = function () {
  IX = null;
  if (!S || window.manualUiOnly) return;
  if (typeof manualTyping === "undefined" || !manualTyping) ensureWorkspace();
  desktopDirty = true;
  desktopPending = true;
  desktopEditVersion++;
  renderStatus();
  clearTimeout(desktopTimer);
  desktopTimer = setTimeout(() => desktopFlush(true).catch(() => {}), 700);
};
async function desktopFlush(force = true) {
  if (!force) return;
  clearTimeout(desktopTimer);
  if (desktopSaving)
    return desktopSaving.then((r) => (desktopDirty ? desktopFlush(true) : r));
  if (!desktopDirty) return;
  desktopSaving = (async () => {
    let audit;
    try {
      if (typeof manualFlushAudit === "function") audit = manualFlushAudit();
      const version = desktopEditVersion,
        state = JSON.parse(JSON.stringify(S));
      const r = await nativeCall("save", {
        state,
        revision: desktopRevision,
        baseState: desktopSavedState,
        baseHeads: desktopSavedHeads,
        user: APP.user,
      });
      acceptFolder(r, state);
      audit = null;
      desktopDirty = desktopEditVersion !== version;
      desktopPending = desktopDirty;
      desktopError = "";
      return r;
    } catch (e) {
      if (typeof manualRestoreAudit === "function") desktopError = e.message;
      throw e;
    } finally {
      desktopSaving = null;
      renderStatus();
    }
  })();
  return desktopSaving;
}
renderStatus = () => {
  if (!S) return;
  const n = folderWarnings.length + folderConflicts.length,
    text =
      desktopError ||
      (desktopSaving
        ? "Сохранение…"
        : desktopDirty
          ? "Есть несохранённые изменения"
          : "Сохранено в папке базы");
  const html = `<span class="si">${ic(desktopError || n ? "warn" : "check")}${esc(text)}</span>${desktopDirty ? B("Сохранить изменения", "desktopSave", "", "pri sm") : ""}${desktopRemoteWaiting ? '<span class="small">Есть изменения других инженеров</span>' : ""}${n ? B(n + " замечаний", "nav", 'data-h="#/sync"', "sm") : ""}<span class="grow"></span><span class="si">${S.projects.length} объекта</span>`;
  if ($("#status").innerHTML !== html) $("#status").innerHTML = html;
};

A.showInFolder = async () => {
  try {
    await nativeCall("openFolder");
  } catch (e) {
    toast(e.message);
  }
};
A.openBlob = async (d) => {
  try {
    await nativeCall("openAsset", { key: d.key });
  } catch (e) {
    modal("Файл не открыт", "<p>" + esc(e.message) + "</p>", [
      { l: "Закрыть" },
    ]);
  }
};
A.pickPdf = async (d) => {
  if (!guard(entKey(d.ent, d.id))) return;
  try {
    const f = await desktopTrack(nativeCall("pickAny"));
    if (!f) return;
    const o = getEnt(d.ent, d.id),
      t = d.p ? getPath(o, d.p) : o;
    if (!t) return;
    Object.assign(t, { file: f.name, fileKey: f.id, pages: f.pages });
    if ("stamped" in t) t.stamped = false;
    commit("Загружен документ «" + f.name + "»", o);
    await desktopFlush();
    render();
  } catch (e) {
    toast(e.message);
  }
};
A.schemeFile = async (d) => {
  if (!guard("sys:" + d.s)) return;
  try {
    const f = await nativeCall("pickPdf");
    if (!f) return;
    const s = getEnt("sys", d.s),
      sc = s.scheme;
    Object.assign(sc, {
      file: f.name,
      fileKey: f.id,
      pages: f.pages,
      stamped: false,
      updated: nowStr(),
      updatedBy: APP.user,
    });
    commit("Загружена схема", s);
    await desktopFlush();
    render();
  } catch (e) {
    toast(e.message);
  }
};
A.desktopSave = async () => {
  try {
    await desktopFlush(true);
    render();
  } catch (e) {
    modal("Изменения не сохранены", "<p>" + esc(e.message) + "</p>", [
      { l: "Закрыть" },
    ]);
  }
};
A.baseSwitch = async () => {
  try {
    await desktopFlush();
    await nativeCall("switchFolder");
  } catch (e) {
    toast(e.message);
  }
};
const folderOldSettings = V.settings;
V.settings = (r) => {
  const tab = r[1] || "general";
  if (tab !== "general") return folderOldSettings(r);
  const nav = tabs("#/settings", tab, [
    ["general", "Основное"],
    ["trash", "Корзина", S.trash.length],
  ]);

  return `<div class="page">${hdr("Настройки приложения", "Папка базы и восстановление")}${nav}<div class="card"><h3>Папка базы</h3><p>${esc(APP.current)}</p><div class="row">${B("Открыть папку", "showInFolder")}${B("Выбрать другую", "baseSwitch")}${B("Сохранить сейчас", "desktopSave", "", "pri")}</div><p class="small mut mt">Карточки, документы, шаблоны и профили читаются из этой папки. Для Яндекс Диска включите хранение файлов базы на компьютере.</p></div><div class="card"><h3>Инженер</h3>${F("Имя", "app", "", "user", APP.user, { rr: 1 })}${B(S.ui.ro ? "Включить редактирование" : "Только просмотр", "roToggle")}</div><div class="card">${B("Синхронизация и восстановление карточек", "nav", 'data-h="#/sync"')}</div></div>`;
};
V.sync = () =>
  `<div class="page">${hdr("Проверка базы", "Текущие карточки и файлы", B("Обновить", "folderRefresh", "", "pri"))}<div class="card">Перед сборкой дождитесь завершения синхронизации Яндекс Диска. Если одна карточка изменена на двух компьютерах, сохранение остановится: обновите базу и повторите изменение.</div>${folderWarnings.map((w) => `<div class="card"><h3>${esc(w.message)}</h3><p>${esc(w.path)}</p>${w.key ? B("Исправить карточку", "folderRepair", `data-key="${esc(w.key)}"`) : ""}</div>`).join("")}${!folderWarnings.length ? '<div class="card">Ошибок карточек и файлов не обнаружено.</div>' : ""}</div>`;
A.folderRefresh = async () => {
  try {
    await desktopFlush();
    acceptFolder(await nativeCall("poll"));
    render();
  } catch (e) {
    toast(e.message);
  }
};

for (const name of [
  "resetDemo",
  "importJson",
  "exportJson",
  "impRun",
  "simLock",
  "simStale",
  "simChange",
  "simConflict",
])
  A[name] = () => toast("Эта функция недоступна в рабочей базе.");
window.desktopReady = false;
window.removeEventListener("hashchange", originalRenderWorkspace);
window.addEventListener("hashchange", () => render());
new QWebChannel(qt.webChannelTransport, async (channel) => {
  desktop = channel.objects.desktop;
  if (desktop.asyncReply)
    desktop.asyncReply.connect((id, raw) => {
      const handler = desktopReplies.get(id);
      desktopReplies.delete(id);
      if (handler) handler(raw);
    });
  desktop.flushRequested.connect(async () => {
    desktopClosing = true;
    try {
      document.activeElement?.blur();
      closeModal();
      if (typeof desktopAuditDirty !== "undefined" && desktopAuditDirty) save();
      await desktopFlush(true);
      await Promise.all([...desktopJobs]);
      await desktopFlush(true);
      desktop.flushDone(true);
    } catch (e) {
      desktopClosing = false;
      desktopError = e.message;
      renderStatus();
      modal(
        "Не удалось сохранить при закрытии",
        "<p>" + esc(e.message) + "</p>",
        [{ l: "Вернуться к работе" }],
      );
      desktop.flushDone(false);
    }
  });
  try {
    const r = await nativeCall("load");
    APP.user = APP.user || "Инженер ПТО";
    APP.current = r.root;
    APP.recent = [];
    S = emptyDesktop();
    desktopUiDefaults = structuredClone(S.ui);
    acceptFolder(r);
    if (!location.hash) location.replace("#/home");
    if (!r.state) {
      save();
      await desktopFlush(true);
    }
    render();
    window.desktopReady = true;
    if (desktop.folderChanged)
      desktop.folderChanged.connect(async () => {
        if (desktopClosing || folderPolling || desktopSaving) return;
        if (desktopDirty) {
          desktopRemoteWaiting = true;
          renderStatus();
          return;
        }
        if (document.querySelector(".dlg")) {
          desktopRemoteWaiting = true;
          renderStatus();
          return;
        }
        folderPolling = true;
        try {
          if (await desktopPollFolder()) render();
        } catch (e) {
          desktopError = e.message;
          renderStatus();
        } finally {
          folderPolling = false;
        }
      });
  } catch (e) {
    document.body.innerHTML =
      '<main style="padding:40px"><h1>Папка не открыта</h1><p>' +
      esc(e.message) +
      "</p></main>";
  }
});
