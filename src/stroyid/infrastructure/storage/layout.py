"""Deterministic card and asset naming, independent of persistence."""

import hashlib, re
from pathlib import Path
from .records import LABELS, safe, portable_path


class CardLayout:
    def __init__(self, paths):
        self.paths = paths
        self._path_plan_cache = {}

    def _title(self, r):
        if r["kind"] == "projects":
            return r["data"].get("name") or r["data"].get("short") or "Объект"
        d = r["data"]
        return (
            d.get("short")
            or d.get("name")
            or d.get("num")
            or d.get("fioShort")
            or d.get("code")
            or LABELS.get(r["field"], "Карточка")
        )

    def _record_path(self, key, r, records):
        cache = getattr(self, "_path_plan_cache", None)
        if cache is None:
            return self._compute_record_path(key, r, records)
        if key not in cache:
            cache[key] = self._compute_record_path(key, r, records)
        return cache[key]

    def _compute_record_path(self, key, r, records):
        if key == "root":
            return "_Служебное/Настройки/База.json"
        kind = r["kind"]
        d = r["data"]
        if kind in ("history", "builds", "volume"):
            return (
                "_Служебное/Настройки/"
                + {"history": "История", "builds": "Сборки", "volume": "Составы"}[kind]
                + "/"
                + hashlib.sha256(key.encode()).hexdigest()[:16]
                + ".json"
            )
        if kind == "trash":
            return portable_path(
                Path("_Служебное/Корзина")
                / (safe(d.get("name") or self._title(r)) + " (" + safe(d["id"])[:20] + ")")
                / "Удалённое.json"
            )

        def display(x):
            v = x["data"]
            return safe(
                (v.get("code") + " — " + v.get("name", ""))
                if x["kind"] == "systems" and v.get("code")
                else self._title(x)
            )

        def sibling_name(parent, name):
            def group(x):
                v = x["data"]
                return (
                    x.get("parent"),
                    v.get("executionId")
                    if kind == "systems"
                    else v.get("orgId")
                    if kind in ("people", "orders")
                    else "",
                )

            peers = sorted(
                k
                for k, x in records.items()
                if x
                and x.get("kind") == kind
                and group(x) == group(r)
                and display(x).casefold() == name.casefold()
            )
            assigned = {}
            used = set()
            for k in peers:
                previous = Path(str(self.paths.get(k, "")).replace("\\", "/")).parent.name
                if (
                    previous.casefold() == name.casefold()
                    or re.fullmatch(
                        re.escape(name) + r" \([2-9]\d*\)|" + re.escape(name) + r" \(1\d+\)",
                        previous,
                        re.I,
                    )
                ) and previous.casefold() not in used:
                    assigned[k] = previous
                    used.add(previous.casefold())
            for k in peers:
                if k in assigned:
                    continue
                index = 1
                candidate = name
                while candidate.casefold() in used:
                    index += 1
                    candidate = name + " (" + str(index) + ")"
                assigned[k] = candidate
                used.add(candidate.casefold())
            return assigned.get(key, name)

        parent = r["parent"]
        name = safe(
            (d.get("code") + " — " + d.get("name", ""))
            if kind == "systems" and d.get("code")
            else self._title(r)
        )
        name = sibling_name(parent, name)
        if kind == "projects":
            base = Path()
            if name.casefold() in ("_служебное", "справочники"):
                name += " (объект)"
        elif kind == "executions":
            base = Path(self._record_path(parent, records[parent], records)).parent
        elif kind == "systems":
            ek = "executions:" + d.get("executionId", "")
            pr = records.get(ek)
            base = (
                Path(self._record_path(ek, pr, records)).parent
                if pr
                else Path(self._record_path(parent, records[parent], records)).parent
                / "Выполнение 1"
            )
        elif parent == "root":
            section = {
                "base": "Материалы и паспорта",
                "orgs": "Организации и подписанты",
                "people": "Организации и подписанты/Представители",
                "orders": "Организации и подписанты/Приказы",
                "profiles": "Профили и шаблоны/Профили",
                "templates": "Профили и шаблоны/Шаблоны Word",
            }.get(kind, LABELS.get(kind, kind))
            base = Path("Справочники") / section
            if kind in ("people", "orders") and d.get("orgId"):
                ok = "orgs:" + d["orgId"]
                if records.get(ok):
                    base = Path(self._record_path(ok, records[ok], records)).parent / LABELS[kind]
        else:
            pr = records.get(parent) or self.latest.get(parent)
            base = Path(self._record_path(parent, pr, records)).parent
            if pr["kind"] == "projects":
                base /= "Общие документы"
            base /= LABELS.get(kind, kind)
        filename = "Материал.json" if kind in ("materials", "base") else "Карточка.json"
        return portable_path(base / name / filename)

    def _context(self, r, records):
        p = s = a = None
        cur = r
        while cur:
            if cur["kind"] == "projects":
                p = cur["data"]
            if cur["kind"] == "systems":
                s = cur["data"]
            if cur["kind"] == "acts":
                a = cur["data"]
            cur = records.get(cur.get("parent"))
        return p, s, a

    def _file_name(self, r, node, trail, records, ext):
        p, s, a = self._context(r, records)
        kind = r["kind"]
        label = node.get("name") or node.get("cap") or node.get("type") or self._title(r)
        if trail and trail[0] == "scheme":
            prefix = "Схема"
            label = "Исполнительная схема"
        elif "schemes" in trail:
            prefix = "Схема"
        elif "tests" in trail or kind == "trials":
            prefix = "Испытание"
        elif "photos" in trail:
            prefix = "Фото"
        elif "scan" in trail:
            prefix = a.get("type", "АОСР") if a else "Подписанный акт"
            label = "Подписанный"
        elif "frameTemplate" in trail:
            prefix = "Шаблон рамки"
        elif kind in ("base", "materials"):
            prefix = node.get("type", "Документ качества")
            label = (
                r["data"].get("name", "Материал")
                + "_"
                + node.get("num", "")
                + "_"
                + node.get("date", "")
            )
        elif kind == "templates":
            prefix = "Шаблон"
            label = r["data"].get("name", "Word")
        else:
            prefix = LABELS.get(kind, "Документ")
        parts = [prefix, s.get("code") if s else "", a.get("num") if a else "", label]
        value = "_".join(str(x) for x in parts if x)
        value = re.sub(r"[\s.\-]+", "_", value)
        value = re.sub("_+", "_", value).strip("_")
        return safe(value)[:130] + ext.lower()
