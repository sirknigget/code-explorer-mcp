from __future__ import annotations

from pathlib import Path

from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.server import create_mcp_server


def main() -> None:
    runtime_config = RuntimeConfig.from_project_root(Path.cwd())
    mcp = create_mcp_server(runtime_config=runtime_config)
    mcp.run()


if __name__ == "__main__":
    main()
