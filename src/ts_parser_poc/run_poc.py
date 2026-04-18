from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

POC_ROOT = Path(__file__).resolve().parent
NODE_MODULES = POC_ROOT / "node_modules"
BRIDGE = POC_ROOT / "ts_parser_bridge.mjs"
EXAMPLE_FILE = POC_ROOT / "example.ts"


def ensure_ready() -> None:
    if not shutil.which("node"):
        raise RuntimeError(
            "Node.js is required for the ts-morph parser POC. "
            "Install Node.js, run `uv run ts-parser-poc-setup`, then rerun `uv run ts-parser-poc`."
        )

    if not NODE_MODULES.exists():
        raise RuntimeError(
            "Node dependencies are not installed for the ts-morph parser POC. "
            "Run `uv run ts-parser-poc-setup` after `uv sync`, then rerun `uv run ts-parser-poc`."
        )


def parse_example() -> dict:
    return parse_file(filename=EXAMPLE_FILE)


def parse_file(*, filename: Path) -> dict:
    ensure_ready()
    payload = {"filename": str(filename)}
    completed = subprocess.run(
        ["node", str(BRIDGE)],
        cwd=POC_ROOT,
        check=True,
        text=True,
        capture_output=True,
        input=json.dumps(payload),
    )
    if completed.stdout:
        return json.loads(completed.stdout)
    raise RuntimeError(completed.stderr or "Node bridge produced no output")


def main() -> None:
    result = parse_file(filename=EXAMPLE_FILE)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
