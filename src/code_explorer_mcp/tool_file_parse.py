from __future__ import annotations

from code_explorer_mcp.models import (
    ParseFileRequest,
    ParseFileToolResponse,
    ToolPlaceholderError,
)
from code_explorer_mcp.parser_registry import DEFAULT_PARSER_REGISTRY
from code_explorer_mcp.parsing.common import select_symbol_types
from code_explorer_mcp.runtime_config import RuntimeConfig
from code_explorer_mcp.utils.paths import ProjectPathError, project_relative_path


def _supported_parse_symbol_types() -> tuple[str, ...]:
    supported_symbol_types: list[str] = []
    for parser_symbol_types in DEFAULT_PARSER_REGISTRY.list_capabilities().values():
        supported_symbol_types.extend(parser_symbol_types)
    return tuple(supported_symbol_types)


SUPPORTED_PARSE_SYMBOL_TYPES: tuple[str, ...] = _supported_parse_symbol_types()


def parse_file(
    request: ParseFileRequest,
    *,
    runtime_config: RuntimeConfig,
) -> ParseFileToolResponse:
    project_root = runtime_config.project_root

    try:
        relative_filename = project_relative_path(project_root, request.filename)
        file_path = project_root / relative_filename
        parser = DEFAULT_PARSER_REGISTRY.get_for_filename(relative_filename)
        source = file_path.read_text(encoding="utf-8")
        parsed = parser.parse_file(relative_filename, source)
        requested_symbol_types = select_symbol_types(
            parsed.available_symbol_types,
            request.content,
        )
    except ProjectPathError as exc:
        return ParseFileToolResponse(
            filename=request.filename,
            language="unknown",
            available_symbol_types=(),
            error=ToolPlaceholderError(
                code="invalid_path",
                message=str(exc),
            ),
        )
    except OSError as exc:
        return ParseFileToolResponse(
            filename=request.filename,
            language="unknown",
            available_symbol_types=(),
            error=ToolPlaceholderError(
                code="file_read_error",
                message=f"Failed to read file {request.filename}: {exc}",
            ),
        )
    except ValueError as exc:
        return ParseFileToolResponse(
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
    return ParseFileToolResponse(
        filename=parsed.filename,
        language=parsed.language,
        available_symbol_types=tuple(parsed.available_symbol_types),
        sections=sections,
        error=None,
    )
