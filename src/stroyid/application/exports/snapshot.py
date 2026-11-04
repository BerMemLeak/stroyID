"""An explicit, self-contained assembly snapshot: editable database and rendered PDF."""

from pathlib import Path
import os
import tempfile
import zipfile
from .jobs import prepare_many, write_many


def write_snapshot(store, state, plans, target):
    target = Path(target).resolve()
    if target.is_relative_to(store.root):
        raise ValueError("Сохраните снимок вне рабочей папки базы")
    if store.invalid or store.missing or store.conflicts:
        raise ValueError("Перед созданием снимка устраните ошибки базы")
    prepared = prepare_many(store, plans)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a complete archive; leave an existing snapshot intact on failure.
    with tempfile.TemporaryDirectory(prefix=".stroyid-snapshot-", dir=target.parent) as temp:
        temp = Path(temp)
        base, pdfs, result = temp / "base.zip", temp / "pdfs.zip", temp / "snapshot.zip"
        store.portable_export(state, base)
        write_many(store, plans, prepared, pdfs)
        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as output:
            for source, prefix in ((base, ""), (pdfs, "Печать/")):
                with zipfile.ZipFile(source) as archive:
                    for item in archive.infolist():
                        output.writestr(prefix + item.filename, archive.read(item))
        with zipfile.ZipFile(result) as archive:
            if archive.testzip() is not None:
                raise ValueError("Не удалось проверить снимок сборки")
        os.replace(result, target)
    return {
        "path": str(target),
        "pages": sum(p["pages"] for p in prepared),
        "documents": sum(p["documents"] for p in prepared),
        "files": len(plans),
    }
