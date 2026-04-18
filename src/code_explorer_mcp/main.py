from __future__ import annotations

from pathlib import Path

from code_explorer_mcp.runtime_context import configure_runtime_root
from code_explorer_mcp.server import mcp


def main() -> None:
    configure_runtime_root(Path.cwd())
    mcp.run()


if __name__ == "__main__":
    main()
