from __future__ import annotations

from fastmcp import FastMCP

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    FetchSymbolResponse,
    GetProjectStructureRequest,
    GetProjectStructureResponse,
    ParseFileRequest,
    ParseFileResponse,
)
from code_explorer_mcp.tool_file_parse import parse_file
from code_explorer_mcp.tool_project_structure import get_project_structure
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol

mcp = FastMCP("code-explorer-mcp")


@mcp.tool(
    name="get_project_structure",
    description=(
        "Return a deterministic project structure view and language capability "
        "discovery for the selected subtree."
    ),
)
def get_project_structure_tool(
    subfolder: str | None = None,
    pattern: str | None = None,
) -> GetProjectStructureResponse:
    request = GetProjectStructureRequest(subfolder=subfolder, pattern=pattern)
    return get_project_structure(request)


@mcp.tool(
    name="parse_file",
    description=(
        "Parse a supported file into a deterministic language-specific envelope."
    ),
)
def parse_file_tool(
    filename: str,
    content: dict[str, bool] | None = None,
) -> ParseFileResponse:
    request = ParseFileRequest(filename=filename, content=content)
    return parse_file(request)


@mcp.tool(
    name="fetch_symbol",
    description=(
        "Fetch the exact source code for a parser-known symbol from a supported "
        "file."
    ),
)
def fetch_symbol_tool(filename: str, symbol: str) -> FetchSymbolResponse:
    request = FetchSymbolRequest(filename=filename, symbol=symbol)
    return fetch_symbol(request)
