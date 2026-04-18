from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NODE_RUNTIME_ROOT = PROJECT_ROOT / "src" / "code_explorer_mcp" / "parsing"
PACKAGE_JSON = NODE_RUNTIME_ROOT / "package.json"


def ensure_node_runtime() -> None:
    if shutil.which("node") and shutil.which("npm"):
        return

    raise RuntimeError(
        "Node.js and npm are required for the TypeScript parser setup. "
        "Please install Node.js first, then rerun `uv run code-explorer-mcp-node-setup`."
    )


def install_node_dependencies() -> None:
    ensure_node_runtime()
    subprocess.run(
        ["npm", "install", "--no-fund", "--no-audit"],
        cwd=NODE_RUNTIME_ROOT,
        check=True,
        text=True,
    )


def main() -> None:
    if not PACKAGE_JSON.exists():
        raise RuntimeError(f"Missing package.json at {PACKAGE_JSON}")
    install_node_dependencies()
    print("Installed Node dependencies for src/code_explorer_mcp/parsing.")


if __name__ == "__main__":
    main()
