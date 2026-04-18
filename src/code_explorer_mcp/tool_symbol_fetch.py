from __future__ import annotations

from code_explorer_mcp.models import (
    FetchSymbolRequest,
    FetchSymbolResponse,
    ToolPlaceholderError,
)


SUPPORTED_FETCH_SYMBOL_TYPES: tuple[str, ...] = ()


def fetch_symbol(request: FetchSymbolRequest) -> FetchSymbolResponse:
    return FetchSymbolResponse(
        filename=request.filename,
        language="unknown",
        symbol=request.symbol,
        symbol_type=None,
        code=None,
        error=ToolPlaceholderError(
            code="not_implemented",
            message=(
                "fetch_symbol is not implemented yet in this task. "
                "This composition-root skeleton only registers the tool contract."
            ),
        ),
    )
