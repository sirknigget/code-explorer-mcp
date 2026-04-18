from __future__ import annotations

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    FetchSymbolResponse,
    ToolPlaceholderError,
)
from code_explorer_mcp.tool_file_parse import PARSER_REGISTRY, PROJECT_ROOT
from code_explorer_mcp.utils.paths import ProjectPathError, resolve_project_path, to_relative_path

SUPPORTED_FETCH_SYMBOL_TYPES: tuple[str, ...] = ()


def fetch_symbol(request: FetchSymbolRequest) -> FetchSymbolResponse:
    try:
        file_path = resolve_project_path(PROJECT_ROOT, request.filename)
        relative_filename = to_relative_path(PROJECT_ROOT, file_path)
        parser = PARSER_REGISTRY.get_for_filename(relative_filename)
        source = file_path.read_text(encoding="utf-8")
        match = parser.fetch_symbol(relative_filename, source, request.symbol)
    except ProjectPathError as exc:
        return FetchSymbolResponse(
            filename=request.filename,
            language="unknown",
            symbol=request.symbol,
            symbol_type=None,
            code=None,
            error=ToolPlaceholderError(
                code="invalid_path",
                message=str(exc),
            ),
        )
    except ValueError as exc:
        return FetchSymbolResponse(
            filename=request.filename,
            language="unknown",
            symbol=request.symbol,
            symbol_type=None,
            code=None,
            error=ToolPlaceholderError(
                code="unsupported_request",
                message=str(exc),
            ),
        )

    if match is None:
        return FetchSymbolResponse(
            filename=relative_filename,
            language=parser.language(),
            symbol=request.symbol,
            symbol_type=None,
            code=None,
            error=ToolPlaceholderError(
                code="symbol_not_found",
                message=f"Symbol not found: {request.symbol}",
            ),
        )

    return FetchSymbolResponse(
        filename=match.filename,
        language=match.language,
        symbol=match.symbol,
        symbol_type=match.symbol_type,
        code=match.code,
        error=None,
    )
