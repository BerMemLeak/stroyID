"""Native command handlers; WebChannel transport lives in bridge.py."""

from __future__ import annotations
from stroyid.resources import UI_ROOT
import shutil
import tempfile
from pathlib import Path
from PySide6.QtCore import QUrl, QSettings
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
from PySide6.QtPdf import QPdfDocument
from stroyid.infrastructure.storage import validate_state


class DesktopCommands:
    def __init__(self, bridge):
        self.bridge, self.store, self.window = bridge, bridge.store, bridge.window
        self.handlers = {
            "load": self.handle_load,
            "validate": self.handle_validate,
            "save": self.handle_save,
            "pickPdf": self.handle_pickPdf,
            "poll": self.handle_poll,
            "repairCard": self.handle_repairCard,
            "cardData": self.handle_cardData,
            "pickAny": self.handle_pickAny,
            "pickImage": self.handle_pickImage,
            "switchFolder": self.handle_switchFolder,
            "pickDocx": self.handle_pickDocx,
            "sampleDocx": self.handle_sampleDocx,
            "saveGeneratedDocx": self.handle_saveGeneratedDocx,
            "openWordTemplate": self.handle_openWordTemplate,
            "openFilledWord": self.handle_openWordTemplate,
            "openAsset": self.handle_openAsset,
            "openFolder": self.handle_openFolder,
            "previewDrawing": self.handle_previewDrawing,
            "saveFrameTemplate": self.handle_saveFrameTemplate,
            "frameFontStatus": self.handle_frameFontStatus,
            "pickFrameFont": self.handle_pickFrameFont,
            "referenceTemplate": self.handle_referenceTemplate,
            "pickFrameTemplate": self.handle_pickFrameTemplate,
            "trashMove": self.handle_trashMove,
            "trashRestore": self.handle_trashMove,
            "trashPurge": self.handle_trashMove,
            "recoverMissing": self.handle_trashMove,
            "saveMaterialsTemplate": self.handle_saveMaterialsTemplate,
            "previewMaterialsImport": self.handle_previewMaterialsImport,
            "commitMaterialsImport": self.handle_commitMaterialsImport,
            "exportPrintFolder": self.handle_exportPrintFolder,
            "exportSnapshot": self.handle_exportSnapshot,
            "exportPortable": self.handle_exportPortable,
            "exportPdfZip": self.handle_exportPortable,
            "exportRegistry": self.handle_exportPortable,
            "exportPdf": self.handle_exportPdf,
        }

    def execute(self, operation, params):
        handler = self.handlers.get(operation)
        if handler is None:
            raise ValueError("Неизвестная команда")
        return handler(params, operation)

    def handle_load(self, params, operation):
        value = self.store.load()
        return value

    def handle_validate(self, params, operation):
        value = validate_state(params["state"])
        return value

    def handle_save(self, params, operation):
        value = self.store.save(
            params["state"], params["revision"], params.get("baseState"), params.get("baseHeads")
        )
        return value

    def handle_pickPdf(self, params, operation):
        name, _ = QFileDialog.getOpenFileName(
            self.window, "Выберите исходный PDF", "", "PDF (*.pdf)"
        )
        if not name:
            value = None
        else:
            doc = QPdfDocument(self.bridge)
            error = doc.load(name)
            if error != QPdfDocument.Error.None_:
                doc.deleteLater()
                raise ValueError(
                    "PDF не открыт. Проверьте файл; защищённые PDF пока не поддерживаются."
                )
            pages = doc.pageCount()
            doc.close()
            doc.deleteLater()
            value = self.store.import_file(name)
            value["pages"] = pages
        return value

    def handle_poll(self, params, operation):
        value = self.store.load()
        return value

    def handle_repairCard(self, params, operation):
        value = self.store.repair(params["key"], params["data"])
        return value

    def handle_cardData(self, params, operation):
        value = self.store.latest.get(params["key"])
        return value

    def handle_pickAny(self, params, operation):
        name, _ = QFileDialog.getOpenFileName(
            self.window,
            "Добавить документ",
            "",
            "Документы (*.pdf *.docx *.doc *.xlsx *.xls *.png *.jpg *.jpeg *.dwg);;Все файлы (*)",
        )
        value = self.store.import_file(name) if name else None
        if value:
            value["pages"] = self.store._pages(Path(name))
        return value

    def handle_pickImage(self, params, operation):
        name, _ = QFileDialog.getOpenFileName(
            self.window, "Фото объекта", "", "Изображения (*.png *.jpg *.jpeg)"
        )
        value = self.store._image(Path(name)) if name else None
        return value

    def handle_switchFolder(self, params, operation):
        name = QFileDialog.getExistingDirectory(self.window, "Папка базы СтройИД")
        if name:
            QSettings().setValue("workspace", name)
            self.window.next_root = name
            self.window.close()
        value = bool(name)
        return value

    def handle_pickDocx(self, params, operation):
        from stroyid.infrastructure.documents.word_templates import inspect_docx

        name, _ = QFileDialog.getOpenFileName(
            self.window, "Загрузить шаблон Word", "", "Word (*.docx)"
        )
        if not name:
            value = None
        else:
            if Path(name).suffix.lower() != ".docx":
                raise ValueError("Выберите шаблон .docx")
            details = inspect_docx(Path(name).read_bytes())
            value = dict(self.store.import_file(name), **details)
        return value

    def handle_sampleDocx(self, params, operation):
        import re
        from stroyid.infrastructure.documents.word_templates import sample_docx, inspect_docx

        if not re.fullmatch(r"[a-z]+", str(params["section"])):
            raise ValueError("Неверный раздел шаблона")
        with tempfile.TemporaryDirectory(prefix="stroiid-sample-") as folder:
            target = Path(folder) / ("Образец_" + str(params["section"]) + ".docx")
            sample_docx(params["section"], params["title"], target)
            value = dict(self.store.import_file(target), **inspect_docx(target.read_bytes()))
        return value

    def handle_saveGeneratedDocx(self, params, operation):
        from stroyid.application.exports.pdf import word_template_path
        from stroyid.infrastructure.documents.word_templates import fill_docx

        source = word_template_path(self.store, params)
        name, _ = QFileDialog.getSaveFileName(
            self.window,
            "Сохранить ведомость",
            Path(params.get("filename", "Ведомость.docx")).name,
            "Word (*.docx)",
        )
        value = None
        if name:
            target = Path(name).with_suffix(".docx").resolve()
            if target == self.store.root or self.store.root in target.parents:
                raise ValueError("Сохраните ведомость вне папки служебных данных")
            with tempfile.TemporaryDirectory(prefix="stroiid-quantity-") as folder:
                filled = Path(folder) / "quantity.docx"
                fill_docx(
                    source.read_bytes(),
                    filled,
                    params.get("values", {}),
                    params.get("collections", {}),
                )
                from stroyid.infrastructure.storage import atomic

                atomic(target, filled.read_bytes())
            value = str(target)
        return value

    def handle_openWordTemplate(self, params, operation):
        import uuid
        from stroyid.infrastructure.documents.word_templates import fill_docx, open_in_word

        source, name = self.store.asset_path(params["key"])
        cache = Path(tempfile.gettempdir()) / "StroyID-preview" / uuid.uuid4().hex
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / (Path(name).stem + ".docx")
        if operation == "openFilledWord":
            fill_docx(
                source.read_bytes(), target, params.get("values", {}), params.get("collections", {})
            )
        else:
            target = source
        value = open_in_word(target)
        return value

    def handle_openAsset(self, params, operation):
        path, name = self.store.asset_path(params["key"])
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            raise ValueError(
                "Система не смогла открыть файл. Назначьте приложение для этого формата."
            )
        value = True
        return value

    def handle_openFolder(self, params, operation):
        value = QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.root)))
        return value

    def handle_previewDrawing(self, params, operation):
        from stroyid.infrastructure.documents.drawing_frame import preview

        value = preview(self.store, params)
        return value

    def handle_saveFrameTemplate(self, params, operation):
        from stroyid.infrastructure.documents.drawing_frame import TEMPLATE

        target, _ = QFileDialog.getSaveFileName(
            self.window, "Сохранить HTML-шаблон рамки", "Рамка_ГОСТ.html", "HTML (*.html)"
        )
        if target:
            Path(target).write_bytes(TEMPLATE.read_bytes())
        value = bool(target)
        return value

    def handle_frameFontStatus(self, params, operation):
        from stroyid.infrastructure.documents.drawing_frame import resolve_frame_font

        try:
            family = resolve_frame_font(
                {"fontKey": params.get("key"), "requireFont": True}, self.store
            )
            value = {"available": True, "family": family}
        except ValueError:
            value = {"available": False}
        return value

    def handle_pickFrameFont(self, params, operation):
        from PySide6.QtGui import QFontDatabase

        name, _ = QFileDialog.getOpenFileName(
            self.window, "Шрифт ISOCPEUR", "", "Шрифты (*.ttf *.otf)"
        )
        value = None
        if name:
            fid = QFontDatabase.addApplicationFont(name)
            families = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
            if not any(f.casefold() == "isocpeur" for f in families):
                if fid >= 0:
                    QFontDatabase.removeApplicationFont(fid)
                raise ValueError("Выбранный файл не содержит шрифт ISOCPEUR")
            value = self.store.import_file(name)
        return value

    def handle_referenceTemplate(self, params, operation):
        from stroyid.infrastructure.documents.word_templates import inspect_docx

        section = params.get("section")
        if section not in ("title", "reg", "quantity", "actRegister"):
            raise ValueError("Неизвестный встроенный шаблон")
        path = (
            UI_ROOT
            / "reference-templates"
            / {
                "title": "title.docx",
                "reg": "registry.docx",
                "quantity": "quantities.docx",
                "actRegister": "act-register.docx",
            }[section]
        )
        value = {**self.store.import_file(path), **inspect_docx(path.read_bytes())}
        return value

    def handle_pickFrameTemplate(self, params, operation):
        from stroyid.infrastructure.documents.drawing_frame import template_svg

        name, _ = QFileDialog.getOpenFileName(self.window, "HTML-шаблон рамки", "", "HTML (*.html)")
        value = None
        if name:
            text = Path(name).read_text("utf-8-sig")
            from stroyid.domain.document_tags import schema

            template_svg(text, {k: "1" for k in schema()["fields"]})
            value = self.store.import_file(name)
        return value

    def handle_trashMove(self, params, operation):
        value = {
            "trashMove": self.store.move_trash,
            "trashRestore": self.store.restore_trash,
            "trashPurge": self.store.purge_trash,
            "recoverMissing": lambda p: self.store.recover_missing(p["key"]),
        }[operation](params)
        return value

    def handle_saveMaterialsTemplate(self, params, operation):
        source = UI_ROOT / "reference-templates/materials-import.xlsx"
        target, _ = QFileDialog.getSaveFileName(
            self.window,
            "Сохранить шаблон импорта материалов",
            "Материалы_шаблон.xlsx",
            "Excel (*.xlsx)",
        )
        value = None
        if target:
            if not target.lower().endswith(".xlsx"):
                target += ".xlsx"
            if Path(target).resolve().is_relative_to(self.store.root):
                raise ValueError("Сохраните шаблон вне рабочей папки базы")
            shutil.copyfile(source, target)
            value = {"path": target}
        return value

    def handle_previewMaterialsImport(self, params, operation):
        from stroyid.application.materials.importer import preview_import

        source, _ = QFileDialog.getOpenFileName(
            self.window, "Выберите Excel с материалами", "", "Excel (*.xlsx)"
        )
        folder = (
            QFileDialog.getExistingDirectory(
                self.window, "Выберите папку с PDF документов качества"
            )
            if source
            else ""
        )
        value = None
        if folder:
            loaded = self.store.load()
            if not loaded["state"]:
                raise ValueError("Сначала создайте базу")
            preview = preview_import(source, folder, loaded["state"])
            from copy import deepcopy

            preview["heads"] = deepcopy(self.store.heads)
            import uuid

            token = uuid.uuid4().hex
            self.material_preview = (token, preview)
            value = {
                "token": token,
                "errors": preview["errors"],
                "items": [
                    {
                        **{k: v for k, v in item.items() if k != "docs"},
                        "docs": [
                            {k: v for k, v in d.items() if k not in ("path", "hash")}
                            for d in item["docs"]
                        ],
                    }
                    for item in preview["items"]
                ],
            }
        return value

    def handle_commitMaterialsImport(self, params, operation):
        from stroyid.application.materials.importer import commit_import

        token, preview = getattr(self, "material_preview", (None, None))
        if token != params.get("token") or preview is None:
            raise ValueError("Повторите проверку Excel")
        value = commit_import(self.store, preview, params.get("choices", {}))
        self.material_preview = (None, None)
        return value

    def handle_exportPrintFolder(self, params, operation):
        from stroyid.application.exports.jobs import prepare_many
        from stroyid.application.exports.printing import write_print_folder

        if self.store.conflicts or self.store.invalid or self.store.missing:
            raise ValueError("Перед экспортом устраните ошибки базы")
        prepared = prepare_many(self.store, params["plans"])
        parent = QFileDialog.getExistingDirectory(
            self.window, "Выберите папку для сохранения печатного комплекта"
        )
        value = None
        if parent:
            from datetime import datetime

            name = "Печать_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            value = write_print_folder(
                self.store, prepared, Path(parent) / name, params.get("options")
            )
        return value

    def handle_exportSnapshot(self, params, operation):
        from stroyid.application.exports.snapshot import write_snapshot

        target, _ = QFileDialog.getSaveFileName(
            self.window,
            "Сделать снимок сборки",
            Path(params.get("filename") or "Снимок_сборки.zip").name,
            "ZIP (*.zip)",
        )
        value = None
        if target:
            if not target.lower().endswith(".zip"):
                target += ".zip"
            value = write_snapshot(self.store, params["state"], params["plans"], target)
        return value

    def handle_exportPortable(self, params, operation):
        if self.store.conflicts or self.store.invalid or self.store.missing:
            raise ValueError(
                "Перед экспортом устраните конфликты и восстановите отсутствующие или повреждённые карточки."
            )
        filename = Path(params.get("filename") or "Комплект.zip").name
        if operation == "exportPortable":
            target, _ = QFileDialog.getSaveFileName(
                self.window, "Сохранить переносимый комплект", filename, "ZIP (*.zip)"
            )
            if target and not target.lower().endswith(".zip"):
                target += ".zip"
            value = self.store.portable_export(params["state"], target) if target else None
        elif operation == "exportPdfZip":
            from stroyid.application.exports.jobs import prepare_many, write_many

            prepared = prepare_many(self.store, params["plans"])
            target, _ = QFileDialog.getSaveFileName(
                self.window, "Сохранить отдельные PDF в ZIP", filename, "ZIP (*.zip)"
            )
            if target and not target.lower().endswith(".zip"):
                target += ".zip"
            value = write_many(self.store, params["plans"], prepared, target) if target else None
        else:
            from stroyid.application.exports.pdf import prepare_export
            from stroyid.application.exports.jobs import write_registry

            prepared = prepare_export(self.store, params["plan"])
            fmt = params.get("format", "xlsx")
            target, _ = QFileDialog.getSaveFileName(
                self.window,
                "Сохранить реестр по фактическим страницам",
                filename,
                "Excel (*.xlsx)" if fmt == "xlsx" else "CSV (*.csv)",
            )
            value = None
            if target:
                if Path(target).resolve().is_relative_to(self.store.root):
                    raise ValueError("Сохраните реестр вне рабочей папки базы")
                if not target.lower().endswith("." + fmt):
                    target += "." + fmt
                write_registry(prepared, target, fmt)
                value = {
                    "path": target,
                    "pages": prepared["pages"],
                    "documents": prepared["documents"],
                }
        return value

    def handle_exportPdf(self, params, operation):
        from stroyid.application.exports.pdf import prepare_export, write_export

        if (
            self.store.conflicts
            or self.store.invalid
            or self.store.missing
            or any("Ожида" in w["message"] for w in self.store.warnings)
        ):
            raise ValueError(
                "Перед сборкой исправьте карточки или восстановите файлы:\n"
                + "\n".join(
                    dict.fromkeys(
                        [
                            str(self.store.paths.get(k, k))
                            for k in [
                                *self.store.invalid,
                                *self.store.missing,
                                *[c["key"] for c in self.store.conflicts],
                            ]
                        ]
                        + [w["path"] + " — " + w["message"] for w in self.store.warnings]
                    )
                )
            )
        prepared = prepare_export(self.store, params["plan"])
        filename = Path(params.get("filename") or "Комплект_ИД.pdf").name
        target, _ = QFileDialog.getSaveFileName(
            self.window, "Сохранить комплект ИД одним PDF", filename, "PDF (*.pdf)"
        )
        if target:
            if not target.lower().endswith(".pdf"):
                target += ".pdf"
            value = write_export(prepared, target, self.store)
        else:
            value = None
        return value
