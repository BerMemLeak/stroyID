"""Explicit trash operations; no historical versions or snapshots are created."""

import copy, shutil, uuid
from .records import walk, validate_state, stamp
from stroyid.domain.migrations import migrate


class TrashService:
    def __init__(self, repository):
        self.repository = repository

    def _entity(self, state, ent, ident, pid=None):
        libs = {
            "base": "base",
            "org": "orgs",
            "per": "people",
            "ord": "orders",
            "pf": "profiles",
            "tpl": "templates",
        }
        if ent in libs:
            arr = state["lib"][libs[ent]]
            o = next((x for x in arr if x["id"] == ident), None)
            return arr, o, {}
        for p in state["projects"]:
            if pid and p["id"] != pid:
                continue
            if ent == "proj" and p["id"] == ident:
                return state["projects"], p, {"pid": p["id"]}
            for field, typ in [
                ("executions", "exec"),
                ("systems", "sys"),
                ("materials", "mat"),
                ("journals", "jr"),
            ]:
                for o in p.get(field, []):
                    if ent == typ and o["id"] == ident:
                        return (
                            p[field],
                            o,
                            {
                                "pid": p["id"],
                                "eid": o.get("executionId", o["id"] if typ == "exec" else ""),
                                "sid": o["id"] if typ == "sys" else "",
                            },
                        )
            for s in p["systems"]:
                for field, typ in [("acts", "act"), ("aik", "aik"), ("journals", "jr")]:
                    for o in s.get(field, []):
                        if ent == typ and o["id"] == ident:
                            return (
                                s[field],
                                o,
                                {"pid": p["id"], "sid": s["id"], "eid": s.get("executionId", "")},
                            )
        return None, None, {}

    @staticmethod
    def _nested(obj, path):
        for part in path.split(".") if path else []:
            obj = (
                next((x for x in obj if x.get("id") == part[1:]), None)
                if part.startswith("#")
                else obj.get(part)
            )
            if obj is None:
                raise ValueError("Карточка или список больше не существует")
        return obj

    def move_trash(self, params):
        result = (
            self.repository.load()
            if not params.get("preview")
            else {"state": copy.deepcopy(params["state"])}
        )
        state = result["state"]
        if not state:
            raise ValueError("База пуста")
        arr, obj, ctx = self._entity(state, params["ent"], params["id"], params.get("pid"))
        if obj is None:
            raise ValueError("Элемент не найден")
        ent = params["ent"]
        item = copy.deepcopy(obj)
        if params.get("row"):
            owner = obj
            arr = self._nested(owner, params["path"])
            item = next((x for x in arr if x["id"] == params["row"]), None)
            if item is None:
                raise ValueError("Документ не найден")
            ctx.update(parentEnt=ent, parentId=obj["id"], path=params["path"])
            ent = "row"
        elif ent == "exec":
            p = next(p for p in state["projects"] if p["id"] == ctx["pid"])
            item = {
                "execution": item,
                "systems": [s for s in p["systems"] if s.get("executionId") == obj["id"]],
            }
            p["systems"] = [s for s in p["systems"] if s.get("executionId") != obj["id"]]
        project = next((p for p in state["projects"] if p["id"] == ctx.get("pid")), None)
        exe = next(
            (e for e in (project or {}).get("executions", []) if e["id"] == ctx.get("eid")), None
        )
        where = (
            " / ".join(
                x
                for x in (
                    (project or {}).get("name"),
                    (exe or {}).get("name"),
                    obj.get("code") if params["ent"] == "sys" else None,
                )
                if x
            )
            or "Справочник"
        )
        name = (
            (item.get("execution") or item).get("name")
            or item.get("num")
            or item.get("file")
            or "Документ"
        )
        arr.remove(obj if ent != "row" else item)
        ident = "trash-" + uuid.uuid4().hex
        state.setdefault("trash", []).insert(
            0,
            {
                "id": ident,
                "ent": ent,
                "item": item,
                "ctx": ctx,
                "name": name,
                "where": where,
                "ts": stamp(),
                "by": params.get("user") or self.repository.actor,
            },
        )
        return self._edit_result(state, params)

    def _edit_result(self, state, params):
        if params.get("preview"):
            return {
                "state": migrate(validate_state(state)),
                "revision": self.repository.revision,
                "root": str(self.repository.root),
                "preview": True,
                "warnings": self.repository.warnings,
                "conflicts": self.repository.conflicts,
            }
        return self.repository.save(state, self.repository.revision)

    def _restore_item(self, state, tid, params):
        t = next((x for x in state["trash"] if x["id"] == tid), None)
        if not t:
            raise ValueError("Элемент корзины не найден")
        ent = t["ent"]
        ctx = t.get("ctx", {})
        item = copy.deepcopy(t["item"])
        pid = params.get("targetProject") or ctx.get("pid")
        eid = params.get("targetExecution") or ctx.get("eid")
        sid = params.get("targetSystem") or ctx.get("sid")
        p = next((p for p in state["projects"] if p["id"] == pid), None)
        if not p and pid and ent != "proj":
            parent = next(
                (x for x in state["trash"] if x["ent"] == "proj" and x["item"]["id"] == pid), None
            )
            if parent and params.get("restoreParents"):
                self._restore_item(state, parent["id"], params)
                p = next(p for p in state["projects"] if p["id"] == pid)
            else:
                raise ValueError("Объект удалён. Восстановите его либо выберите другой объект.")
        if ent == "sys" and not any(e["id"] == eid for e in p["executions"]):
            parent = next(
                (
                    x
                    for x in state["trash"]
                    if x["ent"] == "exec" and x["item"]["execution"]["id"] == eid
                ),
                None,
            )
            if parent and params.get("restoreParents"):
                self._restore_item(state, parent["id"], params)
            else:
                raise ValueError(
                    "Выполнение удалено. Восстановите его либо выберите другое выполнение."
                )
        if ent == "proj":
            arr = state["projects"]
        elif ent == "exec":
            arr = p["executions"]
            execution = item["execution"]
            systems = item["systems"]
            item = execution
        elif ent == "sys":
            arr = p["systems"]
            item["executionId"] = eid
            for a in item.get("acts", []):
                a["executionId"] = eid
        elif ent == "mat":
            arr = p["materials"]
        elif ent in ("act", "aik", "jr"):
            system = next((s for s in p["systems"] if s["id"] == sid), None)
            if ent == "jr" and not sid:
                arr = p["journals"]
            else:
                if system is None:
                    parent = next(
                        (x for x in state["trash"] if x["ent"] == "sys" and x["item"]["id"] == sid),
                        None,
                    )
                    if parent and params.get("restoreParents"):
                        self._restore_item(state, parent["id"], params)
                        system = next(s for s in p["systems"] if s["id"] == sid)
                    else:
                        raise ValueError(
                            "Система удалена. Восстановите её либо выберите другую систему."
                        )
                arr = system[{"act": "acts", "aik": "aik", "jr": "journals"}[ent]]
                if ent == "act":
                    item["executionId"] = system["executionId"]
        elif ent == "row":
            _, owner, _ = self._entity(state, ctx["parentEnt"], ctx["parentId"])
            if owner is None:
                parent = next(
                    (
                        x
                        for x in state["trash"]
                        if x["ent"] == ctx["parentEnt"] and x["item"].get("id") == ctx["parentId"]
                    ),
                    None,
                )
                if parent and params.get("restoreParents"):
                    self._restore_item(state, parent["id"], params)
                    _, owner, _ = self._entity(state, ctx["parentEnt"], ctx["parentId"])
                if owner is None:
                    raise ValueError("Родительская карточка удалена. Сначала восстановите её.")
            arr = self._nested(owner, ctx["path"])
        else:
            arr = state["lib"][
                {
                    "base": "base",
                    "org": "orgs",
                    "per": "people",
                    "ord": "orders",
                    "pf": "profiles",
                    "tpl": "templates",
                }[ent]
            ]
        if any(x.get("id") == item.get("id") for x in arr):
            raise ValueError("Эта карточка уже восстановлена. Существующие данные не перезаписаны.")
        label = item.get("name") or item.get("num")
        if label and any(
            (ent != "sys" or x.get("executionId") == eid)
            and (
                (x.get("name") or x.get("num")) == label
                or ent == "sys"
                and x.get("code") == item.get("code")
            )
            for x in arr
        ):
            field = "name" if "name" in item else "num"
            item[field] = label + " — восстановлено"
        arr.append(item)
        if ent == "exec":
            p["systems"].extend(systems)
        state["trash"].remove(t)

    def restore_trash(self, params):
        state = (
            copy.deepcopy(params["state"])
            if params.get("preview")
            else self.repository.load()["state"]
        )
        self._restore_item(state, params["id"], params)
        return self._edit_result(state, params)

    def _protected(self, state, t):
        bid = (
            t["item"].get("id")
            if t["ent"] == "base"
            else t.get("ctx", {}).get("parentId")
            if t["ent"] == "row" and t.get("ctx", {}).get("parentEnt") == "base"
            else None
        )
        sources = state["projects"] + [x["item"] for x in state["trash"] if x["id"] != t["id"]]
        if (
            t["ent"] == "row"
            and t.get("ctx", {}).get("parentEnt") == "mat"
            and t["ctx"].get("path") == "docs"
        ):
            mid = t["ctx"]["parentId"]
            if any(n.get("id") == mid for source in sources for n in walk(source)):
                return True
        if bid and any(n.get("baseId") == bid for source in sources for n in walk(source)):
            return True
        ident = t["item"].get("id")
        if not ident:
            return False

        def strings(x):
            if isinstance(x, str):
                yield x
            elif isinstance(x, dict):
                for k, v in x.items():
                    if k != "id":
                        yield from strings(v)
            elif isinstance(x, list):
                for v in x:
                    yield from strings(v)

        needed = set(v for source in sources for v in strings(source))
        for _ in range(10):
            old = len(needed)
            for field, records in state["lib"].items():
                if isinstance(records, list):
                    for record in records:
                        if isinstance(record, dict) and record.get("id") in needed:
                            needed.update(strings(record))
            if len(needed) == old:
                break
        return ident in needed

    def purge_trash(self, params):
        state = (
            copy.deepcopy(params["state"])
            if params.get("preview")
            else self.repository.load()["state"]
        )
        selected = [t for t in state["trash"] if params.get("all") or t["id"] == params.get("id")]
        check_state = copy.deepcopy(state)
        check_state["trash"] = [t for t in state["trash"] if t not in selected]
        if any(self._protected(check_state, t) for t in selected):
            raise ValueError(
                "Элемент используется в объектах. Удалите связи перед окончательным удалением."
            )
        folders = [
            self.repository.path(self.repository.paths["trash:" + t["id"]]).parent
            for t in selected
            if "trash:" + t["id"] in self.repository.paths
        ]
        state["trash"] = [t for t in state["trash"] if t not in selected]
        if params.get("preview"):
            return self._edit_result(state, params)
        result = self.repository.save(state, self.repository.revision)
        for folder in folders:
            if folder.exists():
                shutil.rmtree(folder)
        return result
