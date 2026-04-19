from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    FetchSymbolResponse,
    GetProjectStructureRequest,
    GetProjectStructureResponse,
    ParseFileRequest,
    ParseFileResponse,
)
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_project_structure import get_project_structure
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol


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
    ) -> GetProjectStructureResponse:
        request = GetProjectStructureRequest(subfolder=subfolder, pattern=pattern)
        return get_project_structure(request, runtime_config=runtime_config)

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
    ) -> ParseFileResponse:
        request = ParseFileRequest(filename=filename, content=content)
        return parse_file(request, runtime_config=runtime_config)

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
    ) -> FetchSymbolResponse:
        request = FetchSymbolRequest(filename=filename, symbol=symbol)
        return fetch_symbol(request, runtime_config=runtime_config)

    return mcp
