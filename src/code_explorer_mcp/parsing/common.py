from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class SourcePosition:
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: SourcePosition
    end: SourcePosition


@dataclass(frozen=True, slots=True)
class ParserCapabilities:
    language: str
    symbol_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SymbolSpan:
    symbol: str
    symbol_type: str
    span: SourceSpan


@dataclass(slots=True)
class ParsedFile:
    filename: str
    language: str
    available_symbol_types: list[str]
    sections: dict[str, Any] = field(default_factory=dict)
    symbol_spans: dict[str, SymbolSpan] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "filename": self.filename,
            "language": self.language,
            "available_symbol_types": list(self.available_symbol_types),
        }
        for section_name in self.available_symbol_types:
            if section_name in self.sections:
                payload[section_name] = self.sections[section_name]
        return payload


@dataclass(frozen=True, slots=True)
class SymbolMatch:
    filename: str
    language: str
    symbol: str
    symbol_type: str
    code: str
    span: SourceSpan | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "filename": self.filename,
            "language": self.language,
            "symbol": self.symbol,
            "symbol_type": self.symbol_type,
            "code": self.code,
        }
        if self.span is not None:
            payload["span"] = asdict(self.span)
        return payload


def make_capabilities(
    language: str, symbol_types: list[str] | tuple[str, ...]
) -> ParserCapabilities:
    """Create a deterministic parser capability description."""
    return ParserCapabilities(language=language, symbol_types=tuple(symbol_types))


def ordered_unique(values: list[str] | tuple[str, ...]) -> list[str]:
    """Return values in first-seen order without duplicates."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def select_symbol_types(
    available_symbol_types: list[str] | tuple[str, ...],
    content: Mapping[str, object] | None,
) -> list[str]:
    """Resolve requested symbol types against a parser's capability set."""
    available = ordered_unique(list(available_symbol_types))
    if content is None:
        return available

    unknown = sorted(set(content).difference(available))
    if unknown:
        raise ValueError("Unknown symbol types requested: " + ", ".join(unknown))

    return [symbol_type for symbol_type in available if bool(content.get(symbol_type))]


def make_parsed_file(
    *,
    filename: str,
    language: str,
    available_symbol_types: list[str] | tuple[str, ...],
    sections: Mapping[str, Any] | None = None,
    symbol_spans: Mapping[str, SymbolSpan] | None = None,
) -> ParsedFile:
    """Build a ParsedFile with deterministic section ordering."""
    ordered_symbol_types = ordered_unique(list(available_symbol_types))
    section_map = dict(sections or {})
    ordered_sections = {
        symbol_type: section_map[symbol_type]
        for symbol_type in ordered_symbol_types
        if symbol_type in section_map
    }
    return ParsedFile(
        filename=filename,
        language=language,
        available_symbol_types=ordered_symbol_types,
        sections=ordered_sections,
        symbol_spans=dict(symbol_spans or {}),
    )


def slice_source_span(
    source: str,
    span: SourceSpan,
    *,
    column_to_character_offset: Callable[[str, int], int],
) -> str:
    """Slice source text for a span using parser-specific column units."""
    lines = source.splitlines(keepends=True)
    start_offset = offset_for_position(
        lines,
        span.start,
        column_to_character_offset=column_to_character_offset,
    )
    end_offset = offset_for_position(
        lines,
        span.end,
        column_to_character_offset=column_to_character_offset,
    )
    return source[start_offset:end_offset]


def offset_for_position(
    lines: list[str],
    position: SourcePosition,
    *,
    column_to_character_offset: Callable[[str, int], int],
) -> int:
    """Resolve a line/column pair to a character offset in the full source."""
    if position.line < 1:
        raise ValueError(f"Invalid line number: {position.line}")
    if position.line > len(lines):
        return sum(len(line) for line in lines)

    line_start_offset = sum(len(line) for line in lines[: position.line - 1])
    line_text = lines[position.line - 1]
    column_offset = column_to_character_offset(line_text, position.column)
    return line_start_offset + column_offset
