"""Stage a complete print folder before publishing it beside the selected destination."""

import html
import os
import re
import tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from stroyid.application.exports.pdf import render_html


def page_group(page):
    box = page.cropbox
    w, h = float(box.width) * 25.4 / 72, float(box.height) * 25.4 / 72
    if page.rotation % 180:
        w, h = h, w
    short, long = sorted((w, h))
    name = next(
        (
            n
            for n, a, b in [
                ("А5", 148, 210),
                ("А4", 210, 297),
                ("А3", 297, 420),
                ("А2", 420, 594),
                ("А1", 594, 841),
                ("А0", 841, 1189),
            ]
            if abs(short - a) < 2 and abs(long - b) < 2
        ),
        f"{short:.1f}x{long:.1f}мм",
    )
    return name + ("_альбомная" if w > h else "_книжная")


def numbered_page(page, number, work):
    from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
    from PySide6.QtGui import QFont, QPageSize, QPainter, QPdfWriter

    clone = PdfWriter()
    page = clone.add_page(page)
    page.transfer_rotation_to_content()
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    path = work / "number.pdf"
    writer = QPdfWriter(str(path))
    writer.setResolution(72)
    writer.setPageSize(QPageSize(QSizeF(w, h), QPageSize.Unit.Point))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0))
    painter = QPainter(writer)
    painter.setFont(QFont("Arial", 9))
    painter.drawText(QRectF(0, h - 13, w - 10, 12), Qt.AlignmentFlag.AlignRight, str(number))
    painter.end()
    del painter, writer
    page.merge_page(PdfReader(path).pages[0])
    return page


def write_print_folder(store, prepared_list, target, options=None):
    options = options or {}
    target = Path(target).resolve()
    if target.is_relative_to(store.root):
        raise ValueError("Сохраните печатную папку вне базы СтройИД")
    if target.exists():
        raise ValueError("Выберите новое имя папки: существующая папка не перезаписывается")
    modes = options.get("types", {})
    if any(v not in ("simplex", "duplex") for v in modes.values()):
        raise ValueError("Неверный режим печати")
    if options.get("binding", "long") not in ("long", "short"):
        raise ValueError("Неверная сторона переворота")
    buckets = {}
    total = 0
    documents = 0
    rows = []
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".stroiid-print-", dir=target.parent) as tmp:
            work = Path(tmp)
            ordered = work / "По порядку сборки"
            printer = work / "Для принтера"
            ordered.mkdir()
            printer.mkdir()
            for pi, prepared in enumerate(prepared_list):
                for vi, volume in enumerate(prepared["volumes"]):
                    for di, doc in enumerate(volume["documents"]):
                        documents += 1
                        mode = modes.get(
                            doc.get("type", ""),
                            "duplex" if doc.get("type") == "АОСР" else "simplex",
                        )
                        suffix = (
                            "_двусторонняя_"
                            + (
                                "длинный_край"
                                if options.get("binding", "long") == "long"
                                else "короткий_край"
                            )
                            if mode == "duplex"
                            else "_односторонняя"
                        )
                        name = re.sub(
                            r'[<>:"/\\|?*\x00-\x1f]',
                            "_",
                            doc.get("name") or doc.get("type") or "Документ",
                        ).strip(" .")[:100]
                        one = PdfWriter()
                        one.append(doc["reader"], pages=doc["selection"], import_outline=False)
                        one.write(ordered / f"{documents:04d}_{name}.pdf")
                        one.close()
                        active = None
                        segment = None

                        def finish():
                            if segment is None:
                                return
                            bucket = buckets[segment["bucket"]]
                            segment["end"] = len(bucket.pages)
                            if mode == "duplex" and len(bucket.pages) % 2:
                                page = bucket.pages[-1]
                                bucket.add_blank_page(
                                    float(page.mediabox.width), float(page.mediabox.height)
                                )
                                segment["blank"] = len(bucket.pages)
                            rows.append(segment.copy())

                        for index in doc["selection"]:
                            page = doc["reader"].pages[index]
                            total += 1
                            group = page_group(page) + suffix
                            if group != active:
                                finish()
                                active = group
                                bucket = buckets.setdefault(group, PdfWriter())
                                segment = {
                                    "document": documents,
                                    "name": doc.get("name", ""),
                                    "bucket": group,
                                    "start": len(bucket.pages) + 1,
                                    "logicalStart": total,
                                    "logicalEnd": total,
                                }
                            segment["logicalEnd"] = total
                            if options.get("numberPages"):
                                page = numbered_page(page, total, work)
                            buckets[group].add_page(page)
                        finish()
            for group, writer in buckets.items():
                writer.write(printer / (group + ".pdf"))
            esc = lambda x: html.escape(str(x))
            table = "".join(
                "<tr>"
                + "".join(
                    "<td>" + esc(x) + "</td>"
                    for x in [
                        r["document"],
                        r["name"],
                        f"{r['logicalStart']}–{r['logicalEnd']}",
                        r["bucket"] + ".pdf",
                        f"{r['start']}–{r['end']}",
                        r.get("blank", ""),
                    ]
                )
                + "</tr>"
                for r in rows
            )
            render_html(
                "<h2>Порядок комплектации</h2><p>Печатайте в масштабе 100%, без подгонки под страницу. "
                "Режим и сторона переворота указаны в названиях файлов. Пустые обороты уже добавлены. "
                "Разложите документы по номерам первой колонки. Отдельные PDF находятся в папке «По порядку сборки».</p>"
                '<table border="1" cellspacing="0" width="100%"><thead><tr><th>№</th><th>Документ</th>'
                "<th>Страницы сборки</th><th>Пачка</th><th>Страницы пачки</th><th>Пустой оборот</th></tr></thead><tbody>"
                + table
                + "</tbody></table>",
                work / "Порядок комплектации.pdf",
                landscape=True,
            )
            (work / "number.pdf").unlink(missing_ok=True)
            os.rename(work, target)
    finally:
        for writer in buckets.values():
            writer.close()
    return {
        "path": str(target),
        "documents": documents,
        "pages": total,
        "files": documents + len(buckets) + 1,
    }
