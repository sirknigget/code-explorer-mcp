from __future__ import annotations

from code_explorer_mcp.models import (
    GetProjectStructureRequest,
    GetProjectStructureResponse,
    ToolPlaceholderError,
)


def get_project_structure(
    request: GetProjectStructureRequest,
) -> GetProjectStructureResponse:
    return GetProjectStructureResponse(
        subfolder=request.subfolder,
        pattern=request.pattern,
        error=ToolPlaceholderError(
            code="not_implemented",
            message=(
                "get_project_structure is not implemented yet in this task. "
                "This composition-root skeleton only registers the tool contract."
            ),
        ),
    )
