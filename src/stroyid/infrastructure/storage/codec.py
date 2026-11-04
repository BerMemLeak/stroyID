"""Lossless conversion between a workspace and its current cards."""

import copy, base64
from pathlib import Path
from .records import CHILDREN, IMAGE_FIELDS, walk


class CardCodec:
    @staticmethod
    def _image(p):
        return (
            "data:image/"
            + ("png" if Path(p).suffix.lower() == ".png" else "jpeg")
            + ";base64,"
            + base64.b64encode(Path(p).read_bytes()).decode()
        )

    @staticmethod
    def _pages(p):
        if Path(p).suffix.lower() != ".pdf":
            return 0
        try:
            from pypdf import PdfReader

            return len(PdfReader(p).pages)
        except Exception:
            return 0

    def _assemble(self, records=None, hydrate=True):
        records = records if records is not None else self.latest
        root = records.get("root")
        if not root:
            return None
        s = copy.deepcopy(root["data"])
        s.update(
            projects=[],
            ui=copy.deepcopy(self.ui),
            locks={},
            history=[],
            builds=[],
            trash=[],
            volCfg={},
        )
        for field in ("orgs", "people", "orders", "base", "profiles", "templates"):
            s["lib"][field] = []
        objs = {}
        for key, r in records.items():
            if r is None or key == "root":
                continue
            objs[key] = copy.deepcopy(r["data"])
            for f in CHILDREN.get(r["kind"], []):
                objs[key][f] = []
        for key, v in sorted(
            objs.items(), key=lambda kv: (records[kv[0]].get("position", 100000), kv[0])
        ):
            r = records[key]
            kind = r["kind"]
            field = r["field"]
            parent = r["parent"]
            if kind == "volume":
                s["volCfg"][field] = v
            elif kind in ("history", "builds", "trash"):
                s[field].append(v)
            elif parent == "root":
                (s if field == "projects" else s["lib"]).setdefault(field, []).append(v)
            elif parent in objs:
                objs[parent].setdefault(field, []).append(v)
            else:
                self.warnings.append(
                    {
                        "key": key,
                        "path": self.paths.get(key, key),
                        "message": "Ожидается родительская карточка",
                    }
                )
        if hydrate:
            for node in walk(s):
                for field in IMAGE_FIELDS:
                    value = node.get(field)
                    if isinstance(value, str) and value and not value.startswith("data:"):
                        try:
                            p = self.path(value)
                            if p.is_file():
                                node[field] = self._image(p)
                        except ValueError:
                            pass
        return s
