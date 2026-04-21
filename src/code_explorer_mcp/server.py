from __future__ import annotations

from typing import Annotated, cast

from fastmcp import FastMCP

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    GetProjectStructureRequest,
    ParseFileRequest,
)
from code_explorer_mcp.presentation import (
    present_fetch_symbol,
    present_parse_file,
    present_project_structure,
)
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_project_structure import get_project_structure
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol


def _present_for_fastmcp(payload: object) -> dict[str, object]:
    return cast(dict[str, object], payload)


def create_mcp_server(*, runtime_config: RuntimeConfig) -> FastMCP:
    mcp = FastMCP("code-explorer-mcp")

    @mcp.tool(
        name="get_project_structure",
        description=(
            "Return a deterministic project structure view and language capability "
            "discovery for the selected subtree."
        ),
    )
    def get_project_structure_tool(
        subfolder: Annotated[
            str | None,
            (
                "Optional project-relative folder to inspect. Example: 'src'. "
                "Omit this argument to inspect the project root."
            ),
        ] = None,
        pattern: Annotated[
            str | None,
            (
                "Optional glob pattern or comma-separated glob patterns used to filter "
                "files. Example: '*.py' or '*.ts,*.tsx'. Omit this argument to include "
                "all files."
            ),
        ] = None,
    ) -> dict[str, object]:
        request = GetProjectStructureRequest(subfolder=subfolder, pattern=pattern)
        response = get_project_structure(request, runtime_config=runtime_config)
        return _present_for_fastmcp(present_project_structure(response))

    @mcp.tool(
        name="parse_file",
        description=(
            "Parse a supported file into a deterministic language-specific envelope."
        ),
    )
    def parse_file_tool(
        filename: Annotated[
            str,
            (
                "Project-relative file to parse. Example: "
                "'src/code_explorer_mcp/server.py'."
            ),
        ],
        content: Annotated[
            dict[str, bool] | None,
            (
                "Optional map of section names to booleans that selects which parsed "
                "sections to return. Example: {'functions': True}. Valid section "
                "names come from get_project_structure. Omit this argument to return "
                "all available sections. Unknown section names return an error."
            ),
        ] = None,
    ) -> dict[str, object]:
        request = ParseFileRequest(filename=filename, content=content)
        response = parse_file(request, runtime_config=runtime_config)
        return _present_for_fastmcp(present_parse_file(response))

    @mcp.tool(
        name="fetch_symbol",
        description=(
            "Fetch the exact source code for a parser-known symbol from a supported "
            "file."
        ),
    )
    def fetch_symbol_tool(
        filename: Annotated[
            str,
            (
                "Project-relative file that contains the symbol. Example: "
                "'src/code_explorer_mcp/server.py'."
            ),
        ],
        symbol: Annotated[
            str,
            (
                "Exact symbol name to fetch from the file. Example: "
                "'create_mcp_server'. Use a symbol name returned by parse_file. "
                "If the symbol is not present, the tool returns an error."
            ),
        ],
    ) -> dict[str, object]:
        request = FetchSymbolRequest(filename=filename, symbol=symbol)
        response = fetch_symbol(request, runtime_config=runtime_config)
        return _present_for_fastmcp(present_fetch_symbol(response))

    return mcp
