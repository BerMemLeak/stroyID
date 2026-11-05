"""СтройИД Desktop 0.9.5. Windows packaging entry point."""

from __future__ import annotations
import json
import os
from pathlib import Path
from PySide6.QtCore import QObject, QTimer, QFileSystemWatcher, Signal, Slot


class Bridge(QObject):
    flushRequested = Signal()
    asyncReply = Signal(str, str)
    folderChanged = Signal()

    def __init__(self, store, window):
        super().__init__(window)
        self.store, self.window = store, window
        from .commands import DesktopCommands

        self.commands = DesktopCommands(self)
        from concurrent.futures import ThreadPoolExecutor

        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="StroyID-storage")
        self.watcher = QFileSystemWatcher(self)
        self.watchTimer = QTimer(self)
        self.watchTimer.setSingleShot(True)
        self.watchTimer.setInterval(400)
        self.watcher.fileChanged.connect(lambda _: self.watchTimer.start())
        self.watcher.directoryChanged.connect(lambda _: self.watchTimer.start())
        self.watchTimer.timeout.connect(self.notify_external_change)
        self.watchStamp = None
        self.observedPaths = set()
        self.pausedWatchRequests = set()
        # Some native directory notifications omit in-place writes. On Windows
        # check only metadata periodically; never reload or hash an unchanged DB.
        self.metadataTimer = QTimer(self)
        self.metadataTimer.setInterval(3000)
        self.metadataTimer.timeout.connect(self.notify_external_change)
        if os.name == "nt":
            self.metadataTimer.start()
        self.asyncReply.connect(self.refresh_watches)

    @Slot(str, str, str)
    def requestAsync(self, token, operation, payload):
        if operation == "save":
            try:
                self.release_renamed_project_watches(token, json.loads(payload).get("state", {}))
            except (ValueError, TypeError, AttributeError):
                pass  # The request returns the validation error.

        def complete(future):
            try:
                self.asyncReply.emit(token, future.result())
            except RuntimeError:
                pass

        self.executor.submit(self.request, operation, payload).add_done_callback(complete)

    def release_renamed_project_watches(self, token, state):
        incoming = {p["id"]: p.get("name") for p in state.get("projects", [])}
        roots = [
            self.store.path(self.store.paths[key]).parent
            for key, record in list(self.store.latest.items())
            if record
            and record["kind"] == "projects"
            and incoming.get(record["data"]["id"]) != record["data"].get("name")
        ]
        stale = [
            p
            for p in self.watcher.directories()
            if any(Path(p).is_relative_to(root) for root in roots)
        ]
        if stale:
            self.pausedWatchRequests.add(token)
            self.watcher.removePaths(stale)

    @Slot(str, str)
    def refresh_watches(self, token="", raw=""):
        paused = token in self.pausedWatchRequests
        self.pausedWatchRequests.discard(token)
        if raw:
            response = json.loads(raw)
            value = response.get("value")
            if not paused and (
                not isinstance(value, dict) or "revision" not in value or value.get("preview")
            ):
                return
        paths = {str(self.store.root), str(self.store.service), str(self.store.index_path)}
        # Observe file metadata, but register directory handles only.
        # A watcher must not hold the files which atomic saves replace.
        for key, record in list(self.store.latest.items()):
            if not record or record["kind"] in ("history", "builds", "volume"):
                continue
            card = self.store.path(self.store.paths[key])
            paths.add(str(card))
            from stroyid.infrastructure.storage.records import walk

            for node in walk(record["data"]):
                for field in ("fileKey", "photoKey", "logoKey", "signKey"):
                    if node.get(field):
                        paths.add(str(self.store.path(node[field])))
        for rel in (
            "Справочники/Материалы и паспорта",
            "Справочники/Профили и шаблоны/Шаблоны Word",
        ):
            folder = self.store.root / rel
            if folder.exists():
                paths.add(str(folder))
        for name in list(paths):
            parent = Path(name).parent
            while parent.is_relative_to(self.store.root) and parent != self.store.root:
                if parent.is_relative_to(self.store.service):
                    break
                paths.add(str(parent))
                parent = parent.parent
        observed = set(paths)
        paths = {p for p in paths if Path(p).exists()}
        directories = {p if Path(p).is_dir() else str(Path(p).parent) for p in paths}
        self.observedPaths = observed | directories
        current = set(self.watcher.files() + self.watcher.directories())
        if current - directories:
            self.watcher.removePaths(list(current - directories))
        if directories - current:
            self.watcher.addPaths(list(directories - current))
        self.watchStamp = self.watch_fingerprint()
        if getattr(self.store, "_retired_cleanup_pending", False):
            self.executor.submit(self.store._prune_retired_folders, True)

    def watch_fingerprint(self):
        result = []
        for path in self.observedPaths:
            try:
                st = Path(path).stat()
                result.append((path, st.st_mtime_ns, st.st_ctime_ns, st.st_size))
            except OSError:
                result.append((path, None))
        return tuple(sorted(result))

    @Slot()
    def notify_external_change(self):
        current = self.watch_fingerprint()
        if current != self.watchStamp:
            self.watchStamp = current
            self.folderChanged.emit()

    @Slot(str, str, result=str)
    def request(self, operation, payload):
        try:
            value = self.commands.execute(operation, json.loads(payload))
            if isinstance(value, dict) and "revision" in value:
                value["editHeads"] = self.store.base_heads
            return json.dumps({"ok": True, "value": value}, ensure_ascii=False)
        except Exception as error:
            return json.dumps(
                {"ok": False, "error": str(error), "details": getattr(error, "details", [])},
                ensure_ascii=False,
            )

    @Slot(bool)
    def flushPromptShown(self, shown):
        if self.window.closing:
            if shown:
                self.window.close_timer.stop()
            else:
                self.window.close_timer.start(45000)

    @Slot(bool)
    def flushDone(self, success):
        if self.window.closing:
            self.window.close_timer.stop()
            self.window.closing = False
            if success:
                self.window.allow_close = True
                self.window.close()
            # On failure the WebChannel caller has already shown the detailed
            # error and kept the input. Do not cover it with a second native dialog.
