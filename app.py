"""Stable Windows/macOS launcher; application code lives in src/stroyid."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from stroyid.presentation.desktop.window import main

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from stroyid.presentation.desktop.self_test import run

        raise SystemExit(run(sys.argv[sys.argv.index("--self-test") + 1]))
    raise SystemExit(main())
