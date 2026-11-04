"""Current JSON cards and managed assets. No versions, events or automatic backups."""

from __future__ import annotations
import base64
import copy
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from .records import (
    atomic,
    digest,
    encode,
    flatten,
    portable_path,
    safe,
    stamp,
    validate_state,
    walk,
)
from .codec import CardCodec
from .layout import CardLayout
from .cleanup import EmptyDirectoryCleaner
from .transaction import FileTransaction
from .trash import TrashService
from .validation import describe, check, defaults
from stroyid.domain.migrations import migrate

ASSETS = [
    ("fileKey", "fileHash"),
    ("photoKey", "photoHash"),
    ("logoKey", "logoHash"),
    ("signKey", "signHash"),
]
FORMAT = "stroyid.current.v1"


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.service = self.root / "_Служебное"
        self.service.mkdir(parents=True, exist_ok=True)
        self.index_path = self.service / "Индекс.json"
        self.files = self.service / "Входящие документы"
        self.transaction = FileTransaction(self.root, self.service)
        self.transaction.recover()
        self.actor = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "ПК"
        self.latest, self.paths, self.baseline = {}, {}, {}
        self.heads, self.base_heads = {}, {}
        self.invalid, self.missing, self.warnings, self.conflicts = set(), {}, [], []
        self.ui, self.revision, self.ready = {}, 0, False
        self.metrics = {"loads": 0, "saves": 0, "hashed_files": 0, "parsed_json": 0}
        self._json_cache, self._hash_cache = {}, {}
        self._retired_cleanup_pending = False
        self.trash = TrashService(self)
        if not self.index_path.exists() or self._read_json(self.index_path).get("migrationPending"):
            self._migrate_legacy()

    def path(self, relative):
        path = (self.root / portable_path(relative)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Путь выходит за папку базы")
        return path

    @staticmethod
    def _stamp(path):
        st = path.stat()
        return st.st_mtime_ns, st.st_ctime_ns, st.st_size, st.st_ino

    def _read_json(self, path):
        identity = self._stamp(path)
        cached = self._json_cache.get(path)
        if cached and cached[0] == identity:
            return copy.deepcopy(cached[1])
        value = json.loads(path.read_text("utf-8-sig"))
        self.metrics["parsed_json"] += 1
        self._json_cache[path] = identity, value
        return copy.deepcopy(value)

    def hash_file(self, path):
        path = Path(path)
        identity = self._stamp(path)
        cached = self._hash_cache.get(path)
        if cached and cached[0] == identity:
            return cached[1]
        with path.open("rb") as stream:
            value = hashlib.file_digest(stream, "sha256").hexdigest()
        self.metrics["hashed_files"] += 1
        self._hash_cache[path] = identity, value
        return value

    def _assemble(self, records=None, hydrate=True):
        codec = CardCodec()
        codec.latest = records if records is not None else self.latest
        codec.paths, codec.ui, codec.warnings = self.paths, self.ui, self.warnings
        codec.path = self.path
        return codec._assemble(hydrate=hydrate)

    _image = staticmethod(CardCodec._image)
    _pages = staticmethod(CardCodec._pages)

    def load(self):
        self.metrics["loads"] += 1
        self.transaction.recover()
        self.invalid, self.missing, self.warnings, self.conflicts = set(), {}, [], []
        if not self.index_path.exists():
            self.revision += 1
            self.ready = True
            return self._result(None)
        index = self._read_json(self.index_path)
        if index.get("format") != FORMAT:
            raise ValueError("Неизвестный формат базы СтройИД")
        records, paths = {}, {}
        for key, entry in index["cards"].items():
            paths[key] = entry["path"]
            try:
                data = self._read_json(self.path(entry["path"]))
                if not isinstance(data, dict) or data.get("id") != entry.get("id"):
                    raise ValueError("Не изменяйте поле id")
                if entry.get("schema"):
                    check(data, entry["schema"])
            except (OSError, ValueError) as error:
                self.invalid.add(key)
                self.warnings.append(
                    {
                        "key": key,
                        "path": entry["path"],
                        "missing": not self.path(entry["path"]).exists(),
                        "message": "Повреждена или отсутствует текущая карточка: " + str(error),
                    }
                )
                data = copy.deepcopy(
                    self.baseline.get(key, {}).get(
                        "data",
                        defaults(entry.get("schema", {}))
                        or {"id": entry.get("id"), "name": entry.get("label", "Карточка")},
                    )
                )
                if key == "root":
                    raise ValueError(
                        "Повреждена основная карточка базы. Исправьте JSON или откройте снимок сборки."
                    ) from error
                data["id"] = entry.get("id")
                if "name" in data:
                    data["name"] = entry.get("label", "Карточка")
            records[key] = {
                k: copy.deepcopy(v)
                for k, v in entry.items()
                if k not in ("path", "id", "label", "schema")
            }
            records[key]["data"] = data
        self.latest, self.paths = records, paths
        self.ui = index.get("ui", {})
        if not self.invalid:
            from .discovery import FolderDiscovery

            before = copy.deepcopy(records)
            discovery = FolderDiscovery(self)
            discovery._discover()
            discovery._adopt_files()
            if before != records:
                changes = {}
                for key, record in records.items():
                    if record != before.get(key):
                        changes[paths[key]] = encode(record["data"])
                        index["cards"][key] = {
                            **{k: v for k, v in record.items() if k != "data"},
                            "path": paths[key],
                            "id": record["data"].get("id"),
                            "label": CardLayout(paths)._title(record),
                            "schema": describe(record["data"]),
                        }
                changes[self.index_path.relative_to(self.root).as_posix()] = encode(index)
                self.transaction.commit(changes)
        for key, record in records.items():
            for node in walk(record["data"]):
                for field, _ in ASSETS:
                    if node.get(field) and not self.path(node[field]).is_file():
                        self.missing[key] = node[field]
                        self.warnings.append(
                            {
                                "key": key,
                                "path": node[field],
                                "missing": True,
                                "message": "Не найден текущий файл. Загрузите его заново или откройте снимок сборки.",
                            }
                        )
        self.heads = {key: [digest(record["data"])] for key, record in records.items()}
        self.base_heads = copy.deepcopy(self.heads)
        self.baseline = copy.deepcopy(records)
        self.revision += 1
        self.ready = True
        self._retired = index.get("retiredDirectories", [])
        self._prune_retired_folders()
        if index.get("legacyCleanup") and not self.invalid and not self.missing:
            self._remove_legacy_files(index["legacyCleanup"])
            index.pop("legacyCleanup", None)
            atomic(self.index_path, encode(index))
        return self._result(self._assemble())

    def _result(self, state):
        return {
            "state": state,
            "revision": self.revision,
            "root": str(self.root),
            "warnings": self.warnings,
            "conflicts": [],
        }

    @staticmethod
    def _current_state(state):
        state = migrate(copy.deepcopy(validate_state(state)))
        state["history"], state["builds"], state["locks"] = [], [], {}
        state["meta"]["folderModel"] = 10
        for node in walk(state):
            node.pop("versions", None)
            node.pop("version", None)
            node.pop("rev", None)
            node.pop("_t", None)
            for field in ("img", "photo", "logo", "sign"):
                value = node.get(field)
                key = "fileKey" if field == "img" else field + "Key"
                hash_field = "fileHash" if field == "img" else field + "Hash"
                if isinstance(value, str) and value.startswith("data:image/") and node.get(key):
                    if hashlib.sha256(
                        base64.b64decode(value.split(",", 1)[1])
                    ).hexdigest() == node.get(hash_field):
                        node[field] = node[key]
        return state

    def save(self, state, expected_revision=0, base_state=None, base_heads=None):
        self.metrics["saves"] += 1
        incoming = flatten(self._current_state(state))
        baseline = (
            flatten(self._current_state(base_state))
            if base_state is not None
            else copy.deepcopy(self.baseline)
        )
        self.load()
        if self.invalid or self.missing:
            raise ValueError(
                "Перед сохранением восстановите текущие карточки и файлы. "
                + "\n".join(w["path"] for w in self.warnings)
            )
        remote = copy.deepcopy(self.latest)
        merged = copy.deepcopy(remote)
        for key in set(baseline) | set(incoming):
            old, new, actual = baseline.get(key), incoming.get(key), remote.get(key)
            if new == old:
                continue
            if actual != old and actual != new:
                raise ValueError(
                    "Карточка изменена другим пользователем: "
                    + key
                    + ". Обновите базу перед повторным сохранением."
                )
            if new is None:
                merged.pop(key, None)
            else:
                merged[key] = copy.deepcopy(new)
        for key in list(merged):
            if merged[key]["kind"] in ("history", "builds"):
                del merged[key]
                continue
            for node in walk(merged[key]["data"]):
                node.pop("versions", None)
            node.pop("version", None)
        if "root" in merged:
            merged["root"]["data"]["meta"]["folderModel"] = 10
        oldpaths = dict(self.paths)
        planner = CardLayout(oldpaths)
        paths = {
            key: portable_path(planner._record_path(key, record, merged))
            for key, record in merged.items()
        }
        writes, occupied = {}, {}
        current_assets = {
            node[field]: self.path(node[field])
            for record in remote.values()
            for node in walk(record["data"])
            for field, _ in ASSETS
            if node.get(field)
        }
        by_hash = {self.hash_file(path): path for path in current_assets.values() if path.is_file()}
        for key, record in merged.items():
            self._place_assets(record, paths[key], planner, merged, writes, occupied, by_hash)
            relative = paths[key]
            data = encode(record["data"])
            path = self.path(relative)
            if not path.is_file() or path.read_bytes() != data:
                writes[relative] = data
        refs = {
            node[field]
            for record in merged.values()
            for node in walk(record["data"])
            for field, _ in ASSETS
            if node.get(field)
        }
        deletes = (set(oldpaths.values()) | set(current_assets)) - set(paths.values()) - refs
        # Windows resolves case-only renames to the same file. Never delete a
        # newly written card through its former spelling.
        if os.name == "nt":
            active = {portable_path(p).casefold() for p in set(paths.values()) | refs}
            deletes = {p for p in deletes if portable_path(p).casefold() not in active}
        retired = set(getattr(self, "_retired", [])) | {Path(p).parent.as_posix() for p in deletes}
        cards = {
            key: {
                **{k: v for k, v in record.items() if k != "data"},
                "path": paths[key],
                "id": record["data"].get("id"),
                "label": planner._title(record),
                "schema": describe(record["data"]),
            }
            for key, record in merged.items()
        }
        index = {
            "format": FORMAT,
            "cards": cards,
            "ui": copy.deepcopy(state.get("ui", {})),
            "retiredDirectories": sorted(retired),
        }
        if getattr(self, "_legacy_cleanup", None):
            index["legacyCleanup"] = self._legacy_cleanup
        writes[self.index_path.relative_to(self.root).as_posix()] = encode(index)
        self.transaction.commit(writes, sorted(deletes - set(writes)))
        result = self.load()
        self._prune_retired_folders(True)
        return result

    def _place_assets(self, record, relative, planner, records, writes, occupied, by_hash):
        folder = Path(relative).parent

        def visit(node, trail=()):
            if isinstance(node, list):
                for i, child in enumerate(node):
                    visit(child, trail + (str(i),))
                return
            if not isinstance(node, dict):
                return
            for field in ("img", "photo", "logo", "sign"):
                value = node.get(field)
                if isinstance(value, str) and value.startswith("data:image/"):
                    imported = self._import_bytes(
                        base64.b64decode(value.split(",", 1)[1], validate=True),
                        safe(node.get("cap") or field)
                        + (".png" if "image/png" in value[:30] else ".jpg"),
                    )
                    node["fileKey" if field == "img" else field + "Key"] = imported["id"]
                    node[field] = imported["id"]
            for field, hash_field in ASSETS:
                source_key = node.get(field)
                if not source_key:
                    continue
                source = self.path(source_key)
                if not source.is_file():
                    source = by_hash.get(node.get(hash_field), source)
                if not source.is_file():
                    raise ValueError("Не найден исходный файл: " + source_key)
                sha = self.hash_file(source)
                if (
                    record["kind"] == "materials"
                    and record["data"].get("baseId")
                    and not source.is_relative_to(self.files)
                ):
                    continue
                name = planner._file_name(record, node, trail, records, source.suffix or ".pdf")
                section = (
                    "Схемы к акту"
                    if "schemes" in trail
                    else "Испытания к акту"
                    if "tests" in trail
                    else "Фотографии"
                    if "photos" in trail
                    else ""
                )
                target = folder / section / name
                token = str((record["data"].get("id"), node.get("id") or trail, field))
                if target.as_posix() in occupied and occupied[target.as_posix()] != token:
                    target = target.with_name(
                        target.stem
                        + "_"
                        + hashlib.sha256(token.encode()).hexdigest()[:6]
                        + target.suffix
                    )
                occupied[target.as_posix()] = token
                destination = self.path(target.as_posix())
                if not destination.is_file() or self.hash_file(destination) != sha:
                    writes[target.as_posix()] = source
                node[field], node[hash_field] = target.as_posix(), sha
                if field == "fileKey":
                    node["file"] = target.name
                for text in ("img", "photo", "logo", "sign"):
                    if node.get(text) == source_key or (text == "img" and field == "fileKey"):
                        node[text] = target.as_posix()
            for key, value in list(node.items()):
                if isinstance(value, (dict, list)):
                    visit(value, trail + (key,))

        visit(record["data"])

    def _import_bytes(self, data, name):
        path = self.files / uuid.uuid4().hex / safe(name)
        atomic(path, data)
        return {
            "id": path.relative_to(self.root).as_posix(),
            "name": path.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "created": stamp(),
        }

    def import_file(self, source, name=None):
        path = Path(source)
        return self._import_bytes(path.read_bytes(), name or path.name)

    def asset_path(self, key):
        path = self.path(key)
        if not path.is_file():
            raise ValueError("Файл отсутствует: " + str(key))
        return path, path.name

    def _prune_retired_folders(self, force=False):
        if not getattr(self, "_retired", None):
            return
        pending = EmptyDirectoryCleaner().clean(
            self.root,
            self._retired,
            {self.service} | {self.path(p).parent for p in self.paths.values()},
        )
        self._retired_cleanup_pending = bool(pending)

    def _migrate_legacy(self):
        from .legacy import read_legacy

        legacy = read_legacy(self.root)
        if legacy is None:
            return
        state, records, paths, history = legacy
        self._legacy_cleanup = sorted(
            history
            | {
                "_Служебное/Версии карточек",
                "_Служебное/Резервные копии",
                "_Служебное/Удалённые версии",
                "Служебные данные/Версии карточек",
                "Резервные копии",
                "_Служебное/Настройки/История",
                "_Служебное/Настройки/Сборки",
                "_Служебное/Предыдущая структура",
                "_Служебное/Проекция.json",
                "stroiid.sqlite3",
            }
        )
        for node in walk(self._current_state(state)):
            for field, _ in ASSETS:
                if node.get(field) and not self.path(node[field]).is_file():
                    raise ValueError("Перенос остановлен: не найден текущий файл " + node[field])
        state = self._current_state(state)
        planner = CardLayout(paths)
        current = flatten(state)
        seed = {
            "format": FORMAT,
            "migrationPending": True,
            "cards": {
                key: {
                    **{k: v for k, v in r.items() if k != "data"},
                    "id": r["data"].get("id"),
                    "path": paths[key],
                    "label": planner._title(r),
                }
                for key, r in current.items()
                if key in paths
            },
            "ui": {},
            "retiredDirectories": [],
        }
        atomic(self.index_path, encode(seed))
        try:
            self.load()
            self.save(state, self.revision, base_state=self._assemble(hydrate=False))
        except Exception:
            if (
                self.index_path.exists()
                and self._read_json(self.index_path).get("migrationPending")
                and not self.transaction.journal.exists()
            ):
                self.index_path.unlink(missing_ok=True)
            raise
        self._legacy_cleanup = None

    def _remove_legacy_files(self, history):
        cleanup = list(history) + [
            "_Служебное/Версии карточек",
            "_Служебное/Резервные копии",
            "_Служебное/Удалённые версии",
            "Служебные данные/Версии карточек",
            "Резервные копии",
        ]
        live = {
            self.path(node[f])
            for record in self.latest.values()
            for node in walk(record["data"])
            for f, _ in ASSETS
            if node.get(f)
        }
        for relative in cleanup:
            folder = self.path(relative)
            if not any(p.is_relative_to(folder) for p in live):
                if folder.is_dir():
                    shutil.rmtree(folder)
                elif folder.is_file():
                    folder.unlink()
        self._retired = list(
            set(getattr(self, "_retired", [])) | {Path(p).parent.as_posix() for p in history}
        )
        self._prune_retired_folders(True)

    def move_trash(self, params):
        return self.trash.move_trash(params)

    def restore_trash(self, params):
        return self.trash.restore_trash(params)

    def purge_trash(self, params):
        return self.trash.purge_trash(params)

    def portable_export(self, state, target):
        from .portable import PortableExporter

        return PortableExporter(self).export(state, target)

    def repair(self, key, data):
        if key not in self.paths:
            raise ValueError("Карточка не найдена")
        if data.get("id") != self.latest[key]["data"].get("id"):
            raise ValueError("Не изменяйте поле id")
        check(data, describe(self.latest[key]["data"]))
        atomic(self.path(self.paths[key]), encode(data))
        return self.load()

    def recover_missing(self, key):
        raise ValueError(
            "Резервных копий нет. Загрузите отсутствующий файл или откройте снимок сборки."
        )

    def close(self):
        if self.files.exists() and not any(
            self.path(node[f]).is_relative_to(self.files)
            for record in self.latest.values()
            for node in walk(record["data"])
            for f, _ in ASSETS
            if node.get(f)
        ):
            shutil.rmtree(self.files)
