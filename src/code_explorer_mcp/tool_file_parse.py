from __future__ import annotations

from code_explorer_mcp.models import ParseFileRequest, ParseFileResponse, ToolPlaceholderError
from code_explorer_mcp.runtime_context import get_runtime_root
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.parsing.common import select_symbol_types
from code_explorer_mcp.utils.paths import ProjectPathError, resolve_project_path, to_relative_path

PARSER_REGISTRY = DEFAULT_PARSER_REGISTRY
SUPPORTED_PARSE_SYMBOL_TYPES: tuple[str, ...] = tuple(
    symbol_type
    for symbol_types in PARSER_REGISTRY.list_capabilities().values()
    for symbol_type in symbol_types
)


def parse_file(request: ParseFileRequest) -> ParseFileResponse:
    project_root = get_runtime_root()

    try:
        file_path = resolve_project_path(project_root, request.filename)
        relative_filename = to_relative_path(project_root, file_path)
        parser = PARSER_REGISTRY.get_for_filename(relative_filename)
        source = file_path.read_text(encoding="utf-8")
        parsed = parser.parse_file(relative_filename, source)
        requested_symbol_types = select_symbol_types(
            parsed.available_symbol_types,
            request.content,
        )
    except ProjectPathError as exc:
        return ParseFileResponse(
            filename=request.filename,
            language="unknown",
            available_symbol_types=(),
            error=ToolPlaceholderError(
                code="invalid_path",
                message=str(exc),
            ),
        )
    except OSError as exc:
        return ParseFileResponse(
            filename=request.filename,
            language="unknown",
            available_symbol_types=(),
            error=ToolPlaceholderError(
                code="file_read_error",
                message=f"Failed to read file {request.filename}: {exc}",
            ),
        )
    except ValueError as exc:
        return ParseFileResponse(
            filename=request.filename,
            language="unknown",
            available_symbol_types=(),
            error=ToolPlaceholderError(
                code="unsupported_request",
                message=str(exc),
            ),
        )

    sections = {
        symbol_type: parsed.sections[symbol_type]
        for symbol_type in requested_symbol_types
        if symbol_type in parsed.sections
    }
    return ParseFileResponse(
        filename=parsed.filename,
        language=parsed.language,
        available_symbol_types=tuple(parsed.available_symbol_types),
        sections=sections,
        error=None,
    )
