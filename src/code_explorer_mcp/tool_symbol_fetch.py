from __future__ import annotations

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    FetchSymbolResponse,
    ToolPlaceholderError,
)
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.utils.paths import ProjectPathError, project_relative_path

SUPPORTED_FETCH_SYMBOL_TYPES: tuple[str, ...] = ()


def fetch_symbol(
    request: FetchSymbolRequest,
    *,
    runtime_config: RuntimeConfig,
) -> FetchSymbolResponse:
    project_root = runtime_config.project_root

    try:
        relative_filename = project_relative_path(project_root, request.filename)
        file_path = project_root / relative_filename
        parser = DEFAULT_PARSER_REGISTRY.get_for_filename(relative_filename)
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
    except OSError as exc:
        return FetchSymbolResponse(
            filename=request.filename,
            language="unknown",
            symbol=request.symbol,
            symbol_type=None,
            code=None,
            error=ToolPlaceholderError(
                code="file_read_error",
                message=f"Failed to read file {request.filename}: {exc}",
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
