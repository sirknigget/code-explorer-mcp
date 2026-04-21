from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.server import create_mcp_server


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="code-explorer-mcp")
    parser.add_argument(
        "--path",
        type=Path,
        help="Set the project root and working directory for the MCP server.",
    )
    args = parser.parse_args(argv)

    project_root = Path.cwd() if args.path is None else args.path.expanduser().resolve()
    if not project_root.is_dir():
        parser.error(f"--path must point to an existing directory: {project_root}")

    runtime_config = RuntimeConfig.from_project_root(project_root)
    mcp = create_mcp_server(runtime_config=runtime_config)
    mcp.run()


if __name__ == "__main__":
    main()
