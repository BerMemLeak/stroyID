"""Recoverable roll-forward writes. Temporary payloads are removed after commit.

The journal contains only the in-flight write, never past card versions.
"""

from pathlib import Path
import hashlib
import json
import shutil
import uuid
from .records import atomic, encode


class FileTransaction:
    def __init__(self, root: Path, service: Path):
        self.root, self.service = root, service
        self.journal = service / "Запись.json"
        self.staging = service / "Временная запись"

    def path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Путь записи выходит за папку базы")
        return path

    def commit(self, writes, deletes=()):
        self.recover()
        work = self.staging / uuid.uuid4().hex
        work.mkdir(parents=True)
        entries = []
        try:
            for number, (relative, source) in enumerate(writes.items()):
                target = work / str(number)
                if isinstance(source, Path):
                    shutil.copyfile(source, target)
                else:
                    target.write_bytes(source)
                entries.append(
                    {
                        "target": relative,
                        "source": target.relative_to(self.root).as_posix(),
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    }
                )
            atomic(self.journal, encode({"writes": entries, "deletes": list(deletes)}))
        except Exception:
            if not self.journal.exists():
                shutil.rmtree(work)
            raise
        self.recover()

    def recover(self):
        if not self.journal.exists():
            if self.staging.exists():
                shutil.rmtree(self.staging)
            return
        plan = json.loads(self.journal.read_text("utf-8-sig"))
        for item in plan["writes"]:
            source, target = self.path(item["source"]), self.path(item["target"])
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("Повреждена незавершённая запись. Исходные файлы не удалены.")
            atomic(target, data)
        for relative in plan.get("deletes", []):
            target = self.path(relative)
            if target.is_file():
                target.unlink()
        self.journal.unlink()
        if self.staging.exists():
            shutil.rmtree(self.staging)
