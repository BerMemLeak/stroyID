"""Build the desktop UI deterministically, using Python alone."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def bundle():
    ui = ROOT / "ui"
    names = json.loads((ui / "sources.json").read_text("utf-8"))
    if len(set(names)) != len(names):
        raise ValueError("Duplicate frontend source")
    chunks = []
    for name in names:
        source = (ui / "src" / name).resolve()
        if not source.is_relative_to(ui / "src"):
            raise ValueError("Invalid frontend source")
        text = source.read_text("utf-8").rstrip()
        if source.suffix == ".json":
            text = (
                "const DOCUMENT_TAG_SCHEMA = "
                + json.dumps(json.loads(text), ensure_ascii=False, indent=2)
                + ";"
            )
        chunks.append("// Source: " + name + "\n" + text + "\n")
    return "\n;\n".join(chunks)


if __name__ == "__main__":
    target = ROOT / "ui/dist/app.js"
    content = bundle()
    if "--check" in sys.argv:
        if not target.exists() or target.read_text("utf-8") != content:
            raise SystemExit("UI bundle is outdated. Run python tools/build_frontend.py")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
