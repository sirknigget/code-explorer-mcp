from __future__ import annotations

import runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
POC_ENTRYPOINT = PROJECT_ROOT / "src" / "ts_parser_poc" / "run_poc.py"


def main() -> None:
    runpy.run_path(str(POC_ENTRYPOINT), run_name="__main__")


if __name__ == "__main__":
    main()
