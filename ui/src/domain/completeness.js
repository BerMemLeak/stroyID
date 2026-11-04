/* ---------- проверка комплектности объекта ---------- */
function check(p) {
  const E = [],
    W = [];
  if (!p) return { E, W };
  const mids = new Set(p.materials.map((m) => m.id));
  const usedPf = new Set();
  p.systems.forEach((s) => {
    const SL = "#/s/" + s.id;
    s.subprofiles.forEach((sp) => {
      if (sp.profileId) usedPf.add(sp.profileId);
    });
    const nums = {};
    s.acts.forEach((a) => {
      const L = "#/a/" + a.id,
        N = `${s.code} · ${a.num}`;
      (nums[a.num] = nums[a.num] || []).push(a);
      a.materials.forEach((m) => {
        if (!mids.has(m))
          E.push({ t: `${N}: ссылка на удалённый материал`, l: L + "/mat" });
      });
      a.schemes.forEach((x) => {
        if (!x.file)
          E.push({
            t: `${N}: у схемы «${x.name}» нет файла PDF`,
            l: L + "/att",
          });
      });
      a.tests.forEach((t) => {
        if (!t.file)
          E.push({
            t: `${N}: у приложения «${t.name || "без названия"}» нет файла`,
            l: L + "/att",
          });
      });
      const req = new Set();
      a.subs.forEach((id) => {
        const pf = prof(spOf(s, id)?.profileId);
        pf?.reqFields.forEach((f) => req.add(f));
      });
      req.forEach((f) => {
        if (!String(a[f] || "").trim())
          E.push({
            t: `${N}: не заполнено обязательное поле «${FIELD_NAMES[f]}»`,
            l: L,
          });
      });
      if (!a.subs.length)
        W.push({
          t: `${N}: акт не входит ни в один комплект (подпрофиль) и не попадёт в том`,
          l: L,
        });
      a.materials
        .filter((m) => mids.has(m))
        .forEach((m) => {
          if (!a.aikLinks[m] || !s.aik.some((k) => k.id === a.aikLinks[m]))
            W.push({
              t: `${N}: материал «${mName(pMat(p, m))}» без привязанного АИК`,
              l: L + "/mat",
            });
        });
      if (a.date && a.end && a.date < a.end)
        W.push({
          t: `${N}: дата акта (${fmtD(a.date)}) раньше окончания работ (${fmtD(a.end)})`,
          l: L,
        });
      if (a.start && a.end && a.end < a.start)
        W.push({ t: `${N}: окончание работ раньше начала`, l: L });
      a.subs.forEach((id) => {
        const sp = spOf(s, id);
        DOC_ROLES.forEach((r, i) => {
          if (!signer(a, sp, i))
            W.push({
              t: `${N}: не назначен «${ROLE_SH[i]}» (${sp?.name})`,
              l: L + "/main",
            });
        });
      });
    });
    Object.entries(nums).forEach(([k, v]) => {
      if (v.length > 1)
        W.push({
          t: `${s.code}: повторяется номер ${k} (${v.length} акта)`,
          l: "#/a/" + v[1].id,
        });
    });
    s.aik.forEach((k) => {
      if (!mids.has(k.materialId))
        E.push({
          t: `${s.code} · ${k.num}: ссылка на удалённый материал`,
          l: "#/k/" + k.id,
        });
    });
  });
  p.materials.forEach((m) => {
    if (m.baseId && !baseOf(m))
      E.push({
        t: `Материал ссылается на удалённую позицию базы паспортов`,
        l: "#/m/" + m.id,
      });
    else if (!mDocs(m).length)
      W.push({
        t: `Материал «${mName(m)}» без документов качества`,
        l: "#/m/" + m.id,
      });
  });
  for (let i = 0; i < p.materials.length; i++)
    for (let j = i + 1; j < p.materials.length; j++)
      if (similar(mName(p.materials[i]), mName(p.materials[j])))
        W.push({
          t: `Похожие материалы: «${mName(p.materials[i])}» и «${mName(p.materials[j])}»`,
          l: "#/m/" + p.materials[j].id,
        });
  const files = {};
  const addF = (f, l) => {
    if (f) (files[f] = files[f] || []).push(l);
  };
  p.systems.forEach((s) => {
    addF(s.scheme.file, "#/s/" + s.id + "/scheme");
    s.acts.forEach((a) => {
      a.schemes.forEach((x) => addF(x.file, "#/a/" + a.id + "/att"));
      a.tests.forEach((t) => addF(t.file, "#/a/" + a.id + "/att"));
    });
  });
  Object.entries(files).forEach(([f, v]) => {
    if (v.length > 1)
      W.push({
        t: `Один и тот же PDF «${f}» включён ${v.length} раза`,
        l: v[0],
      });
  });
  S.lib.profiles
    .filter((x) => usedPf.has(x.id))
    .forEach((x) =>
      x.reqDocs.forEach((t) => {
        if (!x.templates.some((id) => tpl(id)?.type === t))
          E.push({
            t: `Профиль «${x.name}»: нет шаблона обязательного документа «${t}»`,
            l: "#/lib/profiles/" + x.id,
          });
      }),
    );
  {
    const lp = maxPath(vObj(p), APP.current);
    if (lp.len > 240)
      W.push({
        t: `Длинный путь к файлу (${lp.len} симв., предел Windows ~260): сократите краткое название объекта или имена файлов — ${cut(lp.path, 90)}`,
        l: "#/p/" + p.id + "/files",
      });
  }
  return { E, W };
}
