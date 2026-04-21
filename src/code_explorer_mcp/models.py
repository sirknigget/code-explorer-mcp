from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, NotRequired, TypedDict, TypeAlias


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


class ToolErrorPayload(TypedDict):
    code: str
    message: str


class ErrorPayload(TypedDict):
    error: ToolErrorPayload


class GetProjectStructureSuccessPayload(TypedDict):
    structure: str
    languages: dict[str, list[str]]


GetProjectStructurePayload: TypeAlias = GetProjectStructureSuccessPayload | ErrorPayload


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


ParseFileSectionsPayload: TypeAlias = dict[str, list[str]]
ParseFilePayload: TypeAlias = ParseFileSectionsPayload | ErrorPayload


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


class FetchSymbolSuccessPayload(TypedDict):
    code: str | None
    symbol_type: NotRequired[str]


FetchSymbolPayload: TypeAlias = FetchSymbolSuccessPayload | ErrorPayload
