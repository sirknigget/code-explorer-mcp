from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolPlaceholderError:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class GetProjectStructureRequest:
    subfolder: str | None = None
    pattern: str | None = None


@dataclass(frozen=True, slots=True)
class GetProjectStructureResponse:
    root: str = "."
    subfolder: str | None = None
    pattern: str | None = None
    structure: str = ""
    languages_present: tuple[str, ...] = ()
    available_symbol_types_by_language: dict[str, tuple[str, ...]] = field(
        default_factory=dict,
    )
    error: ToolPlaceholderError | None = None


@dataclass(frozen=True, slots=True)
class ParseFileRequest:
    filename: str
    content: dict[str, bool] | None = None


@dataclass(frozen=True, slots=True)
class ParseFileResponse:
    filename: str
    language: str
    available_symbol_types: tuple[str, ...]
    sections: dict[str, Any] = field(default_factory=dict)
    error: ToolPlaceholderError | None = None


@dataclass(frozen=True, slots=True)
class FetchSymbolRequest:
    filename: str
    symbol: str


@dataclass(frozen=True, slots=True)
class FetchSymbolResponse:
    filename: str
    language: str
    symbol: str
    symbol_type: str | None
    code: str | None
    error: ToolPlaceholderError | None = None
