"""Current card schema, validation, portable paths and atomic file writes."""

from __future__ import annotations
import copy, hashlib, json, os, re, tempfile, time
from datetime import datetime, timezone
from pathlib import Path


def stamp():
    return datetime.now(timezone.utc).isoformat()


def encode(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")


def digest(x):
    return hashlib.sha256(encode(x)).hexdigest()


def safe(x):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(x)).strip(" .")[:90] or "Без названия"
    if s.upper().split(".")[0] in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *("COM" + str(i) for i in range(10)),
        *("LPT" + str(i) for i in range(10)),
    }:
        s = "_" + s
    return s


def portable_path(value):
    """One representation for repository paths, independent of the host OS."""
    return str(value).replace("\\", "/")


def windows_extended_path(value):
    """Absolute Unicode Win32 path, independent of the LongPathsEnabled setting."""
    import ntpath

    value = ntpath.abspath(str(value))
    if value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


_WINDOWS_RETRY_DELAYS = (0.02, 0.04, 0.08, 0.16, 0.32, 0.5, 0.5, 0.5)


def retry_windows_file_operation(operation):
    """Retry only Windows sharing/access races; never replace by truncating a file."""
    for attempt in range(len(_WINDOWS_RETRY_DELAYS) + 1):
        try:
            return operation()
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == len(
                _WINDOWS_RETRY_DELAYS
            ):
                raise
            time.sleep(_WINDOWS_RETRY_DELAYS[attempt])


def atomic(p, data):
    p = Path(windows_extended_path(p) if os.name == "nt" else p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".sid-", suffix=".tmp", dir=str(p.parent))
    tmp = Path(name)
    original_error = None
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        retry_windows_file_operation(lambda: os.replace(tmp, p))
    except BaseException as exc:
        original_error = exc
        raise
    finally:
        try:
            retry_windows_file_operation(lambda: tmp.unlink(missing_ok=True))
        except OSError as cleanup_error:
            if original_error is None:
                raise
            original_error.add_note(
                "Временный файл пока заблокирован: " + str(tmp) + "; " + str(cleanup_error)
            )


def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)


def validate_state(s):
    if (
        not isinstance(s, dict)
        or s.get("meta", {}).get("v") != 30
        or not isinstance(s.get("lib"), dict)
        or not isinstance(s.get("projects"), list)
    ):
        raise ValueError("Неверный формат базы СтройИД")
    for k in ("orgs", "people", "base", "templates", "profiles"):
        if not isinstance(s["lib"].get(k), list):
            raise ValueError("Неверный справочник " + k)
    for p in s["projects"]:
        for k in ("systems", "materials", "journals", "surveys", "opsDocs"):
            if not isinstance(p.get(k), list):
                raise ValueError("Неполная структура объекта: " + k)
    return s


LABELS = {
    "quality": "Документы качества",
    "projects": "Объекты",
    "executions": "Выполнения",
    "systems": "Системы",
    "materials": "Материалы",
    "acts": "Акты скрытых работ",
    "aik": "Входной контроль",
    "journals": "Журналы",
    "surveys": "Исполнительные съёмки",
    "opsDocs": "Эксплуатация",
    "admin": "Общие документы",
    "sketches": "Исполнительные схемы",
    "trials": "Испытания",
    "orgs": "Организации",
    "people": "Представители",
    "orders": "Приказы и допуски",
    "base": "Материалы и паспорта",
    "profiles": "Профили заказчиков",
    "templates": "Шаблоны Word",
}
CHILDREN = {
    "projects": ["executions", "systems", "materials", "journals", "surveys", "opsDocs", "admin"],
    "systems": ["acts", "aik", "journals", "sketches", "trials"],
}
IMAGE_FIELDS = ("img", "photo", "logo", "sign")


def flatten(s):
    out = {}

    def add(field, parent, value, pos):
        v = copy.deepcopy(value)
        key = field + ":" + str(v["id"])
        for f in CHILDREN.get(field, []):
            for i, c in enumerate(v.pop(f, [])):
                add(f, key, c, i)
        out[key] = {"kind": field, "parent": parent, "field": field, "position": pos, "data": v}

    for i, p in enumerate(s["projects"]):
        add("projects", "root", p, i)
    lib = copy.deepcopy(s["lib"])
    for f in LABELS:
        if isinstance(lib.get(f), list):
            for i, v in enumerate(lib.pop(f)):
                add(f, "root", v, i)
    root = {
        k: copy.deepcopy(v)
        for k, v in s.items()
        if k not in ("projects", "lib", "ui", "locks", "history", "builds", "trash", "volCfg")
    }
    root["lib"] = lib
    out["root"] = {"kind": "root", "parent": "", "field": "", "data": root}
    for k, v in s.get("volCfg", {}).items():
        out["volume:" + k] = {"kind": "volume", "parent": "root", "field": k, "data": v}
    for f in ("history", "builds", "trash"):
        for i, v in enumerate(s.get(f, [])):
            out[f + ":" + str(v.get("id") or digest(v))] = {
                "kind": f,
                "parent": "root",
                "field": f,
                "position": i,
                "data": copy.deepcopy(v),
            }
    return out
