"""Read-only import of the old event format. It never creates a version or backup."""

import copy
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .records import digest, portable_path, validate_state
from .codec import CardCodec
from .validation import check, describe


def read_legacy(root: Path):
    folders = [root / "_Служебное/Версии карточек", root / "Служебные данные/Версии карточек"]
    events = {}
    for folder in folders:
        for path in folder.glob("*.json"):
            event = json.loads(path.read_text("utf-8-sig"))
            events[event["id"]] = event
    if events:
        if any(
            e.get("pruned") or e.get("recordMeta") and not e.get("record")
            for e in events.values()
            if e["id"] not in {p for item in events.values() for p in item.get("parents", [])}
        ):
            raise ValueError(
                "Прежняя база доставлена не полностью. Дождитесь синхронизации; перенос не начат."
            )
        consumed = {parent for event in events.values() for parent in event.get("parents", [])}
        heads = {}
        for ident, event in events.items():
            if ident not in consumed:
                heads.setdefault(event["key"], []).append(event)
        records, paths = {}, {}
        for key, choices in heads.items():
            if len({digest(e.get("record")) for e in choices}) > 1:
                raise ValueError(
                    "В прежней базе есть конфликт: " + key + ". Перенос не начат; файлы сохранены."
                )
            event = max(choices, key=lambda e: (e.get("ts", ""), e["id"]))
            if not event.get("record"):
                continue
            record = copy.deepcopy(event["record"])
            relative = portable_path(event["path"])
            path = (root / relative).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Путь прежней карточки выходит за базу")
            if not path.is_file():
                raise ValueError("Не найдена текущая карточка: " + relative)
            current = json.loads(path.read_text("utf-8-sig"))
            if not isinstance(current, dict) or current.get("id") != record["data"].get("id"):
                raise ValueError("Перенос остановлен: изменён id текущей карточки " + relative)
            check(current, describe(record["data"]), required=False)
            record["data"] = current
            records[key], paths[key] = record, relative
        codec = CardCodec()
        codec.latest, codec.paths, codec.ui, codec.warnings = records, paths, {}, []
        state = validate_state(codec._assemble(hydrate=False))
        if codec.warnings:
            raise ValueError("Неполная прежняя база. Перенос не начат.")
        history_roots = {
            portable_path(Path(e["path"]).parent / "История версий") for e in events.values()
        }
        return state, records, paths, history_roots
    sqlite = root / "stroiid.sqlite3"
    if sqlite.is_file():
        with closing(sqlite3.connect(sqlite.as_uri() + "?mode=ro", uri=True)) as connection:
            row = connection.execute("SELECT payload FROM workspace WHERE id=1").fetchone()
            state = validate_state(json.loads(row[0]))
            mapping = {
                key: ("files/" + key) for key, _ in connection.execute("SELECT id,name FROM assets")
            }
        from .records import walk

        for node in walk(state):
            if node.get("fileKey") in mapping:
                node["fileKey"] = mapping[node["fileKey"]]
        return state, {}, {}, set()
    if any(
        (root / path).exists()
        for path in ("_Служебное/Настройки/База.json", "Служебные данные/База.json")
    ):
        raise ValueError(
            "Не доставлен индекс прежней базы. Дождитесь синхронизации; файлы сохранены."
        )
    return None
