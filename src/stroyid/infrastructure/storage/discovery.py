"""Explicit current-file discovery from the editable database folders."""

import copy, hashlib
from .records import CHILDREN, LABELS, walk


class FolderDiscovery:
    def __init__(self, repository):
        self.repository = repository
        self.root, self.latest, self.paths = repository.root, repository.latest, repository.paths
        self.invalid, self.warnings = repository.invalid, repository.warnings
        self.path, self.hash_file, self._pages = (
            repository.path,
            repository.hash_file,
            repository._pages,
        )

    def _files_in(self, folder):
        return [
            p
            for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower()
            in (".pdf", ".docx", ".doc", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".dwg")
            and not p.name.startswith(("~$", "."))
        ]

    def _discover(self):
        # Retain document discovery from Explorer while avoiding false system/card imports.
        known = {str(self.path(p).parent) for p in self.paths.values()}
        locations = [
            ("root", "base", self.root / "Справочники/Материалы и паспорта"),
            ("root", "templates", self.root / "Справочники/Профили и шаблоны/Шаблоны Word"),
        ]
        for key, r in self.latest.items():
            if r and r["kind"] not in ("root", "trash"):
                for field in CHILDREN.get(r["kind"], []):
                    if field not in ("systems", "executions", "materials"):
                        locations.append(
                            (key, field, self.path(self.paths[key]).parent / LABELS[field])
                        )
        # Core discover is reused with redirected locations through a short isolated implementation.
        for parent, field, base in locations:
            if not base.exists():
                continue
            for folder in list(base.iterdir()):
                if (
                    not folder.is_dir()
                    or str(folder.resolve()) in known
                    or not self._files_in(folder)
                ):
                    continue
                ident = (
                    "auto"
                    + hashlib.sha256(str(folder.relative_to(self.root)).encode()).hexdigest()[:20]
                )
                v = {
                    "id": ident,
                    "name": folder.name,
                    "num": "",
                    "date": "",
                    "file": "",
                    "pages": 0,
                    "note": "",
                }
                if field == "base":
                    v.update(baseId="", category="", brand="", maker="", docs=[])
                elif field == "templates":
                    v.update(
                        type="Иной документ", section="other", tags=[], fileKey="", locked=False
                    )
                elif field == "journals":
                    v.update(kind="Специальный журнал", mode="B", cols=[], rows=[])
                elif field == "acts":
                    continue
                key = field + ":" + ident
                r = {"kind": field, "parent": parent, "field": field, "data": v, "position": 100000}
                path = folder / ("Материал.json" if field == "base" else "Карточка.json")
                if key not in self.latest:
                    self.latest[key] = r
                    self.paths[key] = path.relative_to(self.root).as_posix()

    def _adopt_files(self):
        conflict = set()
        for key, r in list(self.latest.items()):
            if r is None or key in self.invalid or key in conflict:
                continue
            v = copy.deepcopy(r["data"])
            folder = self.path(self.paths[key]).parent
            if not folder.exists():
                continue
            changed = False
            for node in walk(v):
                rel = node.get("fileKey")
                if not rel:
                    continue
                p = self.path(rel)
                if not p.is_file():
                    continue
                sha = self.hash_file(p)
                if sha == node.get("fileHash"):
                    continue
                node["fileHash"] = self.hash_file(p)
                changed = True
                if p.suffix.lower() == ".pdf":
                    node["pages"] = self._pages(p)
                if r["kind"] == "templates" and p.suffix.lower() == ".docx":
                    from stroyid.infrastructure.documents.word_templates import inspect_docx

                    try:
                        node["tags"] = inspect_docx(p.read_bytes())["tags"]
                    except ValueError as ex:
                        self.warnings.append(
                            {
                                "key": key,
                                "path": rel,
                                "message": "Шаблон Word повреждён: " + str(ex),
                            }
                        )
            locations = [(folder, None)] + [
                (folder / name, field)
                for field, name in {
                    "schemes": "Схемы к акту",
                    "tests": "Испытания к акту",
                    "photos": "Фотографии",
                    "attachments": "Дополнительные документы",
                }.items()
                if (folder / name).exists()
            ]
            for loc, field in locations:
                for p in self._files_in(loc):
                    rel = p.relative_to(self.root).as_posix()
                    if any(n.get("fileKey") == rel for n in walk(v)):
                        continue
                    info = {
                        "id": "f" + hashlib.sha256(rel.encode()).hexdigest()[:16],
                        "name": p.stem,
                        "file": p.name,
                        "fileKey": rel,
                        "fileHash": self.hash_file(p),
                        "num": "",
                        "date": "",
                        "pages": self._pages(p),
                    }
                    if r["kind"] in ("materials", "base"):
                        info["type"] = (
                            "Паспорт"
                            if "паспорт" in p.stem.lower()
                            else "Декларация о соответствии"
                            if "деклар" in p.stem.lower()
                            else "Сертификат соответствия"
                        )
                        v.setdefault("docs", []).append(info)
                    elif field:
                        if field == "photos" and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                            info.update(cap=p.stem, img=rel)
                        v.setdefault(field, []).append(info)
                    elif (
                        r["kind"] == "acts"
                        and p.suffix.lower() == ".pdf"
                        and not v.get("scan", {}).get("fileKey")
                    ):
                        v["scan"] = info
                    elif r["kind"] in (
                        "aik",
                        "journals",
                        "sketches",
                        "trials",
                        "surveys",
                        "opsDocs",
                        "admin",
                        "orders",
                        "templates",
                    ) and not v.get("fileKey"):
                        v.update({k: info[k] for k in ("file", "fileKey", "fileHash", "pages")})
                        if r["kind"] == "journals":
                            v["mode"] = "B"
                        if r["kind"] == "templates" and p.suffix.lower() == ".docx":
                            from stroyid.infrastructure.documents.word_templates import inspect_docx

                            try:
                                v["tags"] = inspect_docx(p.read_bytes())["tags"]
                            except ValueError:
                                v["tags"] = []
                    else:
                        v.setdefault("attachments", []).append(info)
                    changed = True
            if changed:
                nr = copy.deepcopy(r)
                nr["data"] = v
                self.latest[key] = nr
