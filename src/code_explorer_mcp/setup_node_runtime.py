from __future__ import annotations

import shutil
import subprocess
from importlib import resources
from pathlib import Path


def ensure_node_runtime() -> None:
    if shutil.which("node") and shutil.which("npm"):
        return

    raise RuntimeError(
        "Node.js and npm are required for the TypeScript parser setup. "
        "Please install Node.js first, then rerun `uv run code-explorer-mcp-node-setup`."
    )


def install_node_dependencies() -> None:
    ensure_node_runtime()
    package_json = resources.files("code_explorer_mcp.parsing").joinpath("package.json")
    with resources.as_file(package_json) as package_json_path:
        subprocess.run(
            ["npm", "install", "--no-fund", "--no-audit"],
            cwd=package_json_path.parent,
            check=True,
            text=True,
        )


def main() -> None:
    package_json = resources.files("code_explorer_mcp.parsing").joinpath("package.json")
    with resources.as_file(package_json) as package_json_path:
        if not package_json_path.exists():
            raise RuntimeError(f"Missing package.json at {package_json_path}")
    install_node_dependencies()
    print("Installed Node dependencies.")


if __name__ == "__main__":
    main()
