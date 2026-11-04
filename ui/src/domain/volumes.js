/* ---------- сборка томов (по одному объекту) ---------- */
function volumeList(p) {
  const v = [
    {
      key: "T1",
      kind: "T1",
      title: "Том 1. Общая документация (объектовая ИД)",
      short: "Том 1",
      sub: "Объектовая ИД",
    },
  ];
  let i = 0;
  sortedSys(p).forEach((s) =>
    s.subprofiles.forEach((sp) => {
      i++;
      v.push({
        key: "T2_" + sp.id,
        kind: "T2",
        title: `Том 2.${i}. ${s.code} — ${s.name}${s.subprofiles.length > 1 ? " (" + sp.name + ")" : ""}`,
        short: `Том 2.${i} ${s.code}`,
        sub: s.subprofiles.length > 1 ? sp.name : s.name,
        s,
        sp,
      });
    }),
  );
  v.push({
    key: "T3",
    kind: "T3",
    title: "Том 3. ИД для эксплуатации",
    short: "Том 3",
    sub: "Для эксплуатации",
  });
  return v;
}
function qItems(m) {
  return mDocs(m).map((d) => ({
    id: "q" + d.id,
    type: d.type,
    name: `${d.type}: ${mName(m)}`,
    nd: `№ ${d.num || "—"} от ${fmtD(d.date)}`,
    pages: +d.pages || 1,
    file: d.file,
    folder: "Документы_качества",
  }));
}
function actItem(a, s) {
  const sc = a.scan?.file;
  return {
    id: "a" + a.id,
    type: a.type + (sc ? " (скан)" : ""),
    name: a.works,
    nd: `№ ${a.num} от ${fmtD(a.date)}`,
    pages: sc ? +a.scan.pages || 2 : 2,
    file: sc || s.code + "_" + a.num + ".pdf",
    ref: "#/a/" + a.id,
  };
}
function blocksFor(p, vol) {
  const B = [];
  const pf = vol.sp ? prof(vol.sp.profileId) : null;
  const rule = pf?.quality || "once";
  const title = {
    key: "title",
    title: "Титульный лист",
    items: [
      {
        id: "title",
        type: "Титульный лист",
        name: vol.title,
        nd: "",
        pages: 1,
        file: "Титульный_лист.docx",
      },
    ],
  };
  const reg = {
    key: "reg",
    title: vol.kind === "T3" ? "Опись" : "Реестр (опись) документов",
    items: [],
    auto: true,
  };
  const jItem = (j) => ({
    id: "j" + j.id,
    type: "Журнал",
    name: j.name,
    nd: j.mode === "B" ? "PDF (скан)" : "По РД-11-05-2007",
    pages: j.mode === "B" ? +j.pages || 1 : 2 + Math.ceil(j.rows.length / 10),
    file: j.mode === "B" ? j.file : slug(j.name) + ".pdf",
    ref: "#/j/" + j.id,
  });
  const mat = (id) => pMat(p, id);
  if (vol.kind === "T1") {
    B.push(title, reg);
    B.push({
      key: "orders",
      title: "Приказы о назначении ответственных лиц, допуски СРО",
      items: S.lib.orders.map((o) => ({
        id: "o" + o.id,
        type: "Приказ / доверенность",
        name: o.name,
        nd: `№ ${o.num} от ${fmtD(o.date)}`,
        pages: +o.pages || 1,
        file: o.file,
      })),
    });
    B.push({
      key: "ozhr",
      title: "Общий журнал работ (ОЖР)",
      items: p.journals.filter((j) => j.kind.startsWith("Общий")).map(jItem),
    });
    B.push({
      key: "spj",
      title: "Специальные журналы объекта",
      items: p.journals.filter((j) => !j.kind.startsWith("Общий")).map(jItem),
    });
    const ms = [
      ...new Set(p.systems.flatMap((s) => s.acts.flatMap((a) => a.materials))),
    ]
      .map(mat)
      .filter(Boolean);
    B.push({
      key: "quality",
      title: "Паспорта, сертификаты, декларации",
      items: ms.flatMap(qItems),
    });
    B.push({
      key: "aook",
      title: "Акты освидетельствования ответственных конструкций (АООК)",
      items: p.systems.flatMap((s) =>
        sortActs(s.acts.filter((a) => a.type === "АООК")).map((a) =>
          actItem(a, s),
        ),
      ),
    });
    B.push({
      key: "survey",
      title: "Исполнительные съёмки (геодезия)",
      items: p.surveys.map((x) => ({
        id: "v" + x.id,
        type: "Исполнительная съёмка",
        name: x.name,
        nd: `№ ${x.num} от ${fmtD(x.date)}`,
        pages: +x.pages || 1,
        file: x.file,
      })),
    });
  } else if (vol.kind === "T2") {
    const s = vol.s;
    const acts = sortActs(
      s.acts.filter((a) => a.type === "АОСР" && a.subs.includes(vol.sp.id)),
    );
    B.push(title, reg);
    B.push({
      key: "aik",
      title: "Акты входного контроля (АИК)",
      items: s.aik.map((k) => ({
        id: "k" + k.id,
        type: "АИК",
        name: "Входной контроль: " + (mName(mat(k.materialId)) || "[удалён]"),
        nd: `№ ${k.num} от ${fmtD(k.date)}`,
        pages: 1,
        file: k.num + ".pdf",
        ref: "#/k/" + k.id,
      })),
    });
    const seen = new Set(),
      ai = [];
    acts.forEach((a) => {
      ai.push(actItem(a, s));
      if (a.photos.length)
        ai.push({
          id: "p" + a.id,
          type: "Фототаблица",
          name: `Фототаблица к ${a.num}`,
          nd: "",
          pages: photoSheets(a),
          file: "Фототаблица_к_" + a.num + ".pdf",
          sub: true,
          ref: "#/a/" + a.id + "/att",
        });
      if (rule !== "once")
        a.materials
          .map(mat)
          .filter(Boolean)
          .forEach((m) => {
            if (rule === "first" && seen.has(m.id)) return;
            seen.add(m.id);
            qItems(m).forEach((q) =>
              ai.push({ ...q, id: q.id + "_" + a.id, sub: true }),
            );
          });
    });
    B.push({
      key: "aosr",
      title:
        "АОСР" +
        (acts.some((a) => a.photos.length) ? " + фототаблицы" : "") +
        (rule !== "once" ? " + документы качества" : ""),
      items: ai,
    });
    const sch = [];
    if (s.scheme.file)
      sch.push({
        id: "ss" + s.id,
        type: "Исполнительная схема",
        name: `Исполнительная схема системы ${s.code}`,
        nd: "общая",
        pages: +s.scheme.pages || 1,
        file: s.scheme.file
          ? s.scheme.file.replace(/\.pdf$/i, "_со_штампом.pdf")
          : "[нет файла]",
        ref: "#/s/" + s.id + "/scheme",
      });
    acts.forEach((a) =>
      a.schemes.forEach((x) =>
        sch.push({
          id: "c" + x.id,
          type: "Исполнительная схема",
          name: x.name,
          nd: "к " + a.num,
          pages: +x.pages || 1,
          file: x.file
            ? x.file.replace(/\.pdf$/i, "_со_штампом.pdf")
            : "[нет файла]",
          ref: "#/a/" + a.id + "/att",
        }),
      ),
    );
    B.push({
      key: "schemes",
      title: "Исполнительные схемы (со штампами)",
      items: sch,
    });
    B.push({
      key: "tests",
      title: "Акты испытаний, протоколы",
      items: acts.flatMap((a) =>
        a.tests.map((t) => ({
          id: "t" + t.id,
          type: "Акт испытаний / протокол",
          name: t.name,
          nd: `№ ${t.num || "—"} от ${fmtD(t.date)}`,
          pages: +t.pages || 1,
          file: t.file || "[нет файла]",
          ref: "#/a/" + a.id + "/att",
        })),
      ),
    });
    B.push({
      key: "spj",
      title: "Специальные журналы системы",
      items: s.journals.map(jItem),
    });
    if (rule === "once") {
      const ms = [...new Set(acts.flatMap((a) => a.materials))]
        .map(mat)
        .filter(Boolean);
      B.push({
        key: "quality",
        title: "Паспорта, сертификаты, декларации",
        items: ms.flatMap(qItems),
      });
    }
  } else {
    B.push(title, reg);
    const eq = p.materials.filter((m) =>
      ["Оборудование", "Отопительный прибор", "Арматура"].includes(
        mF(m, "category"),
      ),
    );
    B.push({
      key: "pass",
      title: "Паспорта на оборудование",
      items: eq.flatMap((m) => qItems(m).filter((q) => q.type === "Паспорт")),
    });
    B.push({
      key: "instr",
      title: "Инструкции, схемы, журналы пусконаладки",
      items: p.opsDocs.map((o) => ({
        id: "op" + o.id,
        type: "Документ для эксплуатации",
        name: o.name,
        nd: o.num ? "№ " + o.num : "",
        pages: +o.pages || 1,
        file: o.file,
      })),
    });
  }
  const cfg = S.volCfg[p.id + "|" + vol.key] || {};
  if (cfg.order)
    B.sort((a, b) => {
      const ia = cfg.order.indexOf(a.key),
        ib = cfg.order.indexOf(b.key);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
  B.forEach((b) => {
    b.off = (cfg.off || []).includes(b.key);
    const ord = (cfg.docs || {})[b.key];
    if (ord)
      b.items.sort((x, y) => {
        const i1 = ord.indexOf(x.id),
          i2 = ord.indexOf(y.id);
        return (i1 < 0 ? 999 : i1) - (i2 < 0 ? 999 : i2);
      });
  });
  const total = B.filter((b) => !b.off && !b.auto).reduce(
    (n, b) => n + b.items.length,
    0,
  );
  const r = B.find((b) => b.auto);
  if (r)
    r.items = [
      {
        id: "reg",
        type: "Реестр",
        name: r.title,
        nd: "",
        pages: Math.max(1, Math.ceil((total + 1) / 22)),
        file: "Реестр.docx",
      },
    ];
  return B;
}
function registry(p, vol) {
  const B = blocksFor(p, vol);
  const rows = [];
  let pg = 1,
    n = 0,
    book = 1;
  const lim = +S.splitPages || 0;
  B.filter((b) => !b.off).forEach((b) =>
    b.items.forEach((it) => {
      if (lim && !rows.length) rows.push({ book: 1 });
      else if (lim && pg - 1 + it.pages > lim && pg > 1) {
        book++;
        pg = 1;
        rows.push({ book });
      }
      n++;
      rows.push({ ...it, n, from: pg, to: pg + it.pages - 1 });
      pg += it.pages;
    }),
  );
  return {
    B,
    rows,
    pages: rows.filter((r) => !r.book).reduce((s, r) => s + r.pages, 0),
    books: book,
  };
}
function folderTree(p, vol) {
  const { B } = registry(p, vol);
  const name = slug(vol.short);
  let out = name + "/\n├── " + name + "_ИД.pdf   (итоговый файл)\n";
  const act = B.filter((b) => !b.off && b.items.length);
  act.forEach((b, i) => {
    const last = i === act.length - 1;
    const no = String(i + 1).padStart(2, "0");
    if (b.key === "title" || b.key === "reg") {
      out +=
        (last ? "└── " : "├── ") +
        no +
        "_" +
        (b.key === "title" ? "Титульный_лист.docx" : "Реестр.docx") +
        "\n";
      return;
    }
    out +=
      (last ? "└── " : "├── ") +
      no +
      "_" +
      slug(b.title.split(" (")[0].split(" +")[0]) +
      "/\n";
    const its = b.items.slice(0, 4);
    its.forEach((it, j) => {
      out +=
        (last ? "    " : "│   ") +
        (j === its.length - 1 && b.items.length <= 4 ? "└── " : "├── ") +
        slug(it.file || it.name) +
        "\n";
    });
    if (b.items.length > 4)
      out +=
        (last ? "    " : "│   ") + "└── … ещё " + (b.items.length - 4) + "\n";
  });
  return out;
}
