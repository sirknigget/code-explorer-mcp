from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, NotRequired, TypedDict


@dataclass(frozen=True, slots=True)
class ToolPlaceholderError:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class GetProjectStructureRequest:
    subfolder: str | None = None
    pattern: str | None = None


@dataclass(frozen=True, slots=True)
class GetProjectStructureToolResponse:
    root: str = "."
    subfolder: str | None = None
    pattern: str | None = None
    structure: str = ""
    languages_present: tuple[str, ...] = ()
    available_symbol_types_by_language: dict[str, tuple[str, ...]] = field(
        default_factory=dict,
    )
    error: ToolPlaceholderError | None = None


class ToolErrorMCPResponse(TypedDict):
    code: str
    message: str


class GetProjectStructureMCPResponse(TypedDict):
    structure: NotRequired[str]
    languages: NotRequired[dict[str, list[str]]]
    error: NotRequired[ToolErrorMCPResponse]


@dataclass(frozen=True, slots=True)
class ParseFileRequest:
    filename: str
    content: dict[str, bool] | None = None


@dataclass(frozen=True, slots=True)
class ParseFileToolResponse:
    filename: str
    language: str
    available_symbol_types: tuple[str, ...]
    sections: dict[str, Any] = field(default_factory=dict)
    error: ToolPlaceholderError | None = None


class ParseFileMCPResponse(TypedDict):
    sections: NotRequired[dict[str, list[str]]]
    error: NotRequired[ToolErrorMCPResponse]


@dataclass(frozen=True, slots=True)
class FetchSymbolRequest:
    filename: str
    symbol: str


@dataclass(frozen=True, slots=True)
class FetchSymbolToolResponse:
    filename: str
    language: str
    symbol: str
    symbol_type: str | None
    code: str | None
    error: ToolPlaceholderError | None = None


class FetchSymbolMCPResponse(TypedDict):
    code: NotRequired[str | None]
    symbol_type: NotRequired[str]
    error: NotRequired[ToolErrorMCPResponse]
