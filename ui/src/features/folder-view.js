/* ---------- файлы базы: как база выглядит на диске ---------- */
function fsName(s, n = 40) {
  s = String(s || "")
    .replace(/[\\/:*?"<>|«»]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (s.length > n) s = s.slice(0, n).trim();
  return s.replace(/[. ]+$/, "") || "Без названия";
}
const objDir = (p) => fsName(p.name, 90);
const sysDir = (s) => s.dir || fsName(s.code, 20);
const actDir = (a) => a.dir || fsName(a.num, 30);
const DIR = (name, kids, ref, note) => ({
  name,
  dir: 1,
  kids: kids.filter(Boolean),
  ref,
  note,
});
const FL = (name, note, ref) => (name ? { name, note, ref } : null);
function lockFiles(key) {
  const L = S.locks[key];
  return L && L.length
    ? DIR(
        ".locks",
        L.map((l) =>
          FL(
            fsName(l.user.replace(/\./g, "").replace(/ /g, "_"), 30) +
              "_" +
              l.pc +
              ".json",
            (isFresh(l) ? "пульс " : "брошена, пульс ") + hm(l.pulse),
          ),
        ),
      )
    : null;
}
function vJr(j) {
  return j.mode === "B"
    ? DIR(
        fsName(j.name),
        [FL("журнал.json", ""), FL(j.file, j.pages + " л.")],
        "#/j/" + j.id,
      )
    : FL(fsName(j.name) + ".json", j.rows.length + " записей", "#/j/" + j.id);
}
function vAct(s, a) {
  return DIR(
    actDir(a),
    [
      FL("акт.json", a.status),
      a.scan?.file
        ? FL(a.scan.file, "скан подписанного акта · " + a.scan.pages + " л.")
        : null,
      a.schemes.length
        ? DIR(
            "Схемы",
            a.schemes.map((x) => FL(x.file, x.pages + " л.")),
          )
        : null,
      a.tests.length
        ? DIR(
            "Испытания",
            a.tests.map((t) => FL(t.file, t.pages + " л.")),
          )
        : null,
      a.photos.length
        ? DIR(
            "Фото",
            a.photos.map((ph, i) =>
              FL(
                "фото_" + String(i + 1).padStart(2, "0") + ".jpg",
                "сжато до 2000 px",
              ),
            ),
          )
        : null,
    ],
    "#/a/" + a.id,
  );
}
function vSys(p, s) {
  const sc = s.scheme;
  return DIR(
    sysDir(s),
    [
      FL("система.json", "" + " · подпрофилей: " + s.subprofiles.length),
      lockFiles("sys:" + s.id),
      DIR(
        "Исполнительная схема",
        [
          FL(sc.file, sc.pages + " л."),
          sc.file && sc.stamped
            ? FL(
                sc.file.replace(/\.pdf$/i, "") + "_со_штампом.pdf",
                "создаётся программой",
              )
            : null,
        ],
        "#/s/" + s.id + "/scheme",
      ),
      ...sortActs(s.acts).map((a) => vAct(s, a)),
      s.aik.length
        ? DIR(
            "АИК",
            s.aik.map((k) =>
              FL(k.num + ".json", mName(pMat(p, k.materialId)), "#/k/" + k.id),
            ),
          )
        : null,
      s.journals.length ? DIR("Журналы", s.journals.map(vJr)) : null,
    ],
    "#/s/" + s.id,
  );
}
function vObj(p) {
  const users = [...new Set(S.history.map((h) => h.user))];
  const bl = (S.builds || []).filter((b) => b.pid === p.id);
  return DIR(
    objDir(p),
    [
      FL("объект.json", ""),
      lockFiles("obj:" + p.id),
      DIR(
        "Материалы",
        p.materials.map((m) =>
          m.baseId
            ? FL(
                fsName(mName(m), 48) + ".json",
                "ссылка на базу паспортов",
                "#/m/" + m.id,
              )
            : DIR(
                fsName(m.name, 48),
                [
                  FL("материал.json"),
                  ...m.docs.map((d) => FL(d.file, d.pages + " л.")),
                ],
                "#/m/" + m.id,
              ),
        ),
      ),
      p.journals.length ? DIR("Журналы", p.journals.map(vJr)) : null,
      ...sortedSys(p).map((s) => vSys(p, s)),
      DIR(
        "_Тома",
        [...new Set(bl.map((b) => b.short))].map((sh) =>
          DIR(
            slug(sh),
            bl
              .filter((b) => b.short === sh)
              .map((b) =>
                FL(
                  b.ts.slice(6, 10) +
                    "-" +
                    b.ts.slice(3, 5) +
                    "-" +
                    b.ts.slice(0, 2) +
                    "_" +
                    slug(sh) +
                    "_ИД.pdf",
                  b.pages + " л. · " + b.by,
                ),
              ),
          ),
        ),
      ),
      DIR(
        "_История",
        users.map((u) =>
          FL(
            fsName(u.replace(/\./g, "").replace(/ /g, "_"), 30) + ".jsonl",
            "журнал действий пользователя",
          ),
        ),
      ),
    ],
    "#/p/" + p.id,
  );
}
function vfs() {
  const L = S.lib;
  return DIR("", [
    FL("база.json", "формат 3.0 · " + S.meta.name),
    DIR(
      "_Справочники",
      [
        FL("организации.json", L.orgs.length + " зап.", "#/lib/orgs"),
        FL("представители.json", L.people.length + " зап.", "#/lib/people"),
        FL("матрица_подписантов.json", "", "#/lib/sign"),
        lockFiles("lib"),
        DIR(
          "Приказы",
          L.orders.map((o) => FL(o.file, o.pages + " л.")),
          "#/lib/orders",
        ),
        DIR(
          "Подписи",
          L.people
            .filter((x) => x.sign)
            .map((x) => FL(fsName(x.fioShort) + ".png")),
        ),
        DIR(
          "База паспортов",
          L.base.map((b) =>
            DIR(
              fsName(b.name, 48),
              [
                FL("паспорт.json"),
                ...b.docs.map((d) => FL(d.file, d.pages + " л.")),
              ],
              "#/lib/base/" + b.id,
            ),
          ),
        ),
        DIR(
          "Профили",
          L.profiles.map((x) =>
            FL(fsName(x.name, 40) + ".json", "", "#/lib/profiles/" + x.id),
          ),
        ),
        DIR(
          "Шаблоны",
          L.templates.map((t) => FL(t.file, t.tags.length + " тегов")),
          "#/lib/templates",
        ),
      ],
      "#/lib/orgs",
    ),
    ...S.projects.map(vObj),
    DIR(
      "_Корзина",
      S.trash.map((t) =>
        FL(fsName(entLabel(t.ent, t.item), 50), "удалено " + t.ts),
      ),
    ),
  ]);
}
function fsFind(segs) {
  let n = vfs();
  for (const s of segs) {
    const k = (n.kids || []).find((x) => x.name === s);
    if (!k) return null;
    n = k;
  }
  return n;
}
const winPath = (segs) =>
  APP.current + (segs.length ? "\\" + segs.join("\\") : "");
const fxHref = (segs) => "#/files/" + segs.map(encodeURIComponent).join("/");
function explorer(segs) {
  const n = fsFind(segs);
  if (!n) return '<div class="empty">Папка не найдена</div>';
  const crumbs = [
    `<a href="#/files">${esc(APP.current)}</a>`,
    ...segs.map(
      (s, i) => `<a href="${fxHref(segs.slice(0, i + 1))}">${esc(s)}</a>`,
    ),
  ].join('<span class="mut">\\</span>');
  const kids = n.kids
    .slice()
    .sort(
      (a, b) =>
        (b.dir ? 1 : 0) - (a.dir ? 1 : 0) ||
        a.name.localeCompare(b.name, "ru", { numeric: true }),
    );
  return `<div class="fx-path">${crumbs}<span class="grow"></span>${B(ic("folder") + "Показать в папке", "showInFolder", `data-path="${esc(winPath(segs))}"`, "sm ghost")}</div>
 ${
   kids.length
     ? `<div class="tw"><table class="tbl"><thead><tr><th>Имя</th><th>Сведения</th><th style="width:230px"></th></tr></thead><tbody>${kids
         .map((k) => {
           const sp = [...segs, k.name];
           return `<tr${k.dir ? ` class="cl" data-a="nav" data-h="${fxHref(sp)}"` : ""}><td><span class="row" style="flex-wrap:nowrap">${ic(k.dir ? "folder" : "file", k.dir ? "ic fxd" : "ic")}<span${k.name.startsWith(".") || k.name.startsWith("_") ? ' class="mut"' : ""}>${esc(k.name)}</span></span></td><td class="t2">${esc(k.note || (k.dir ? k.kids.length + " эл." : ""))}</td>
  <td><div class="row" style="flex-wrap:nowrap;justify-content:flex-end;min-height:30px">${k.ref ? `<a class="btn sm ghost" href="${k.ref}" data-a="nav" data-h="${k.ref}">В программе</a>` : ""}${k.dir ? "" : B("Открыть", "fileOpen", `data-path="${esc(winPath(sp))}"`, "sm ghost")}</div></td></tr>`;
         })
         .join("")}</tbody></table></div>`
     : '<div class="empty">Папка пуста</div>'
 }
 <div class="small mut mt">Файлы данных (.json) пишет программа — вручную их править не нужно. PDF и фото копируются сюда при загрузке. Синхронизацию между компьютерами делает клиент Яндекс Диска.</div>`;
}
V.files = (r) =>
  `<div class="page">${hdr("Папка базы", "Так база выглядит на диске: обычные папки и файлы, их можно открыть в проводнике без программы")}${explorer(r.slice(1))}</div>`;
function maxPath(n, prefix) {
  let best = { len: prefix.length, path: prefix };
  (n.kids || []).forEach((k) => {
    const p = prefix + "\\" + k.name;
    const r = k.dir ? maxPath(k, p) : { len: p.length, path: p };
    if (r.len > best.len) best = r;
  });
  return best;
}
A.showInFolder = (d) => toast(`Откроется проводник: ${d.path || APP.current}`);
A.fileOpen = (d) =>
  toast(
    `Файл откроется в программе по умолчанию: ${String(d.path).split("\\").pop()}`,
  );
