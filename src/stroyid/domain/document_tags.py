"""Shared tag vocabulary, read from the same JSON declaration used by the UI."""

from stroyid.resources import UI_ROOT
import json
from functools import lru_cache


@lru_cache(maxsize=1)
def schema():
    source = (UI_ROOT / "src/domain/document-tags.json").read_text("utf-8")
    return json.loads(source)


def collection_tags():
    return {group + "." + key for group, keys in schema()["collections"].items() for key in keys}


def validate_values(tags, values):
    fields = schema()["fields"]
    unknown = [
        tag
        for tag in tags
        if tag not in fields and not (tag.startswith("ДопПоля.") and tag in values)
    ]
    if unknown:
        raise ValueError(
            "Неизвестные теги: " + ", ".join("{{" + tag + "}}" for tag in sorted(unknown))
        )
    missing = [
        tag
        for tag in tags
        if fields.get(tag, {}).get("required") and not str(values.get(tag, "")).strip()
    ]
    if missing:
        raise ValueError(
            "Не заполнены поля: " + ", ".join("{{" + tag + "}}" for tag in sorted(missing))
        )
