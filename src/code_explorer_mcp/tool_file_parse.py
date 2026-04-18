from __future__ import annotations

from code_explorer_mcp.models import ParseFileRequest, ParseFileResponse, ToolPlaceholderError


SUPPORTED_PARSE_SYMBOL_TYPES: tuple[str, ...] = ()


def parse_file(request: ParseFileRequest) -> ParseFileResponse:
    return ParseFileResponse(
        filename=request.filename,
        language="unknown",
        available_symbol_types=SUPPORTED_PARSE_SYMBOL_TYPES,
        error=ToolPlaceholderError(
            code="not_implemented",
            message=(
                "parse_file is not implemented yet in this task. "
                "This composition-root skeleton only registers the tool contract."
            ),
        ),
    )
