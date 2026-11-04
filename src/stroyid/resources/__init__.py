"""One resource locator for source checkouts and packaged applications."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
UI_ROOT = RESOURCE_ROOT / "ui"
