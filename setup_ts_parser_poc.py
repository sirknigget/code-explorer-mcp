from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
POC_ROOT = PROJECT_ROOT / "src" / "ts_parser_poc"


def ensure_node_runtime() -> None:
    if shutil.which("node") and shutil.which("npm"):
        return

    raise RuntimeError(
        "Node.js and npm are required for the ts-morph parser POC setup. "
        "Please install Node.js first, then rerun `uv run ts-parser-poc-setup`."
    )


def install_node_dependencies() -> None:
    ensure_node_runtime()
    subprocess.run(
        ["npm", "install", "--no-fund", "--no-audit"],
        cwd=POC_ROOT,
        check=True,
        text=True,
    )


def main() -> None:
    install_node_dependencies()
    print("Installed Node dependencies for src/ts_parser_poc.")


if __name__ == "__main__":
    main()
