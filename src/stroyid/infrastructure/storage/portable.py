"""Export an independently editable current-state database."""

import copy, zipfile
from pathlib import Path
from .records import walk, validate_state


class PortableExporter:
    def __init__(self, repository):
        self.repository = repository

    def export(self, state, target):
        """A selected, independently openable folder repository, with all used references."""
        import tempfile
        from .repository import Store

        state = copy.deepcopy(validate_state(state))
        state["history"] = []
        state["builds"] = []
        state["locks"] = {}
        state["ui"] = {}

        def strings(v):
            if isinstance(v, str):
                yield v
            elif isinstance(v, dict):
                for x in v.values():
                    yield from strings(x)
            elif isinstance(v, list):
                for x in v:
                    yield from strings(x)

        needed = set(strings(state["projects"]))
        lib = {
            k: [] for k in ("base", "quality", "orgs", "people", "orders", "profiles", "templates")
        }
        chosen = set()
        original = state["lib"]
        all_trash = state.get("trash", [])
        archived = []
        project_ids = {p["id"] for p in state["projects"]}
        for _ in range(10):
            count = len(archived)
            for t in all_trash:
                if t in archived:
                    continue
                ent = t.get("ent")
                ctx = t.get("ctx", {})
                usable = (
                    ent in ("base", "mat")
                    and t["item"].get("id") in needed
                    or ent == "row"
                    and ctx.get("parentEnt") in ("base", "mat")
                    and ctx.get("parentId") in needed
                )
                if usable and (ent != "mat" or ctx.get("pid") in project_ids):
                    archived.append(t)
                    needed.update(strings(t["item"]))
            if len(archived) == count:
                break
        state["trash"] = archived
        for _ in range(10):
            changed = False
            for field in lib:
                for record in original.get(field, []):
                    if record["id"] in needed and (field, record["id"]) not in chosen:
                        chosen.add((field, record["id"]))
                        lib[field].append(record)
                        needed.update(strings(record))
                        changed = True
            if not changed:
                break
        people = {p["id"] for p in lib["people"]}
        lib["signMatrix"] = {
            k: [x for x in vals if x in people]
            for k, vals in original.get("signMatrix", {}).items()
        }
        state["lib"] = lib
        target = Path(target).resolve()
        if target.is_relative_to(self.repository.root):
            raise ValueError("Сохраните ZIP вне рабочей папки базы")
        with tempfile.TemporaryDirectory(prefix="sid-portable-") as temp:
            root = Path(temp) / "СтройИД"
            dest = Store(root)
            mapping = {}
            for node in walk(state):
                for f, h in [
                    ("fileKey", "fileHash"),
                    ("photoKey", "photoHash"),
                    ("logoKey", "logoHash"),
                    ("signKey", "signHash"),
                ]:
                    rel = node.get(f)
                    if not rel:
                        continue
                    if rel not in mapping:
                        src, _ = self.repository.asset_path(rel)
                        mapping[rel] = dest.import_file(src)["id"]
                    node[f] = mapping[rel]
                    node.pop(h, None)
                    if node.get("img") == rel:
                        node["img"] = mapping[rel]
                    for textfield in ("photo", "logo", "sign"):
                        if node.get(textfield) == rel:
                            node[textfield] = mapping[rel]
            dest.save(state, 0)
            dest.close()
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
                for file in root.rglob("*"):
                    if file.is_file() and not file.is_relative_to(dest.files):
                        z.write(file, "СтройИД/" + file.relative_to(root).as_posix())
        return {"path": str(target), "projects": len(state["projects"])}
