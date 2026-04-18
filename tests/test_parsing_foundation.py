from __future__ import annotations

from dataclasses import dataclass

import pytest

from code_explorer_mcp.parsing.base import Parser, ParserRegistry
from code_explorer_mcp.parsing.common import (
    ParsedFile,
    SourcePosition,
    SourceSpan,
    SymbolMatch,
    SymbolSpan,
    make_parsed_file,
    ordered_unique,
    select_symbol_types,
)


@dataclass(slots=True)
class FakeParser(Parser):
    language_name: str
    extensions: tuple[str, ...]
    symbol_types: list[str]

    def supports(self, filename: str) -> bool:
        return filename.endswith(self.extensions)

    def language(self) -> str:
        return self.language_name

    def available_symbol_types(self) -> list[str]:
        return list(self.symbol_types)

    def parse_file(self, filename: str, source: str) -> ParsedFile:
        return make_parsed_file(
            filename=filename,
            language=self.language_name,
            available_symbol_types=self.symbol_types,
            sections={symbol_type: [filename, source] for symbol_type in self.symbol_types},
        )

    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None:
        if symbol != "target":
            return None
        return SymbolMatch(
            filename=filename,
            language=self.language_name,
            symbol=symbol,
            symbol_type=self.symbol_types[0],
            code=source,
        )



def test_make_parsed_file_orders_sections_by_available_symbol_types() -> None:
    parsed = make_parsed_file(
        filename="sample.py",
        language="python",
        available_symbol_types=["imports", "functions", "imports"],
        sections={"functions": [{"name": "run"}], "imports": [{"module": "os"}]},
    )

    assert parsed.to_dict() == {
        "filename": "sample.py",
        "language": "python",
        "available_symbol_types": ["imports", "functions"],
        "imports": [{"module": "os"}],
        "functions": [{"name": "run"}],
    }



def test_select_symbol_types_returns_requested_true_values_in_capability_order() -> None:
    assert select_symbol_types(
        ["imports", "globals", "functions"],
        {"functions": True, "globals": False, "imports": True},
    ) == ["imports", "functions"]



def test_select_symbol_types_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown symbol types requested: classes"):
        select_symbol_types(["imports", "functions"], {"classes": True})



def test_ordered_unique_preserves_first_seen_order() -> None:
    assert ordered_unique(["imports", "functions", "imports", "classes"]) == [
        "imports",
        "functions",
        "classes",
    ]



def test_symbol_match_to_dict_includes_span_only_when_present() -> None:
    match = SymbolMatch(
        filename="sample.ts",
        language="typescript",
        symbol="Thing",
        symbol_type="interfaces",
        code="export interface Thing {}",
        span=SourceSpan(
            start=SourcePosition(line=1, column=0),
            end=SourcePosition(line=1, column=25),
        ),
    )

    assert match.to_dict() == {
        "filename": "sample.ts",
        "language": "typescript",
        "symbol": "Thing",
        "symbol_type": "interfaces",
        "code": "export interface Thing {}",
        "span": {
            "start": {"line": 1, "column": 0},
            "end": {"line": 1, "column": 25},
        },
    }



def test_parser_registry_resolves_by_filename_and_language() -> None:
    python_parser = FakeParser("python", (".py",), ["imports", "functions"])
    ts_parser = FakeParser("typescript", (".ts", ".tsx"), ["classes", "interfaces"])
    registry = ParserRegistry([python_parser, ts_parser])

    assert registry.list_languages() == ["python", "typescript"]
    assert registry.list_capabilities() == {
        "python": ["imports", "functions"],
        "typescript": ["classes", "interfaces"],
    }
    assert registry.get_for_filename("src/module.py") is python_parser
    assert registry.get_by_language("typescript") is ts_parser
    assert registry.capabilities_for_paths(["src/module.py", "web/app.tsx", "README.md"]) == {
        "python": ["imports", "functions"],
        "typescript": ["classes", "interfaces"],
    }



def test_parser_registry_rejects_duplicate_language_registration() -> None:
    registry = ParserRegistry()
    registry.register(FakeParser("python", (".py",), ["functions"]))

    with pytest.raises(ValueError, match="Parser already registered for language: python"):
        registry.register(FakeParser("python", (".pyi",), ["functions"]))



def test_parser_registry_raises_for_unsupported_file() -> None:
    registry = ParserRegistry([FakeParser("python", (".py",), ["functions"])])

    with pytest.raises(ValueError, match="No parser registered for file: README.md"):
        registry.get_for_filename("README.md")



def test_parsed_file_preserves_symbol_spans_for_later_fetch_use() -> None:
    span = SymbolSpan(
        symbol="run",
        symbol_type="functions",
        span=SourceSpan(
            start=SourcePosition(line=2, column=0),
            end=SourcePosition(line=4, column=0),
        ),
    )
    parsed = make_parsed_file(
        filename="sample.py",
        language="python",
        available_symbol_types=["functions"],
        sections={"functions": [{"name": "run"}]},
        symbol_spans={"run": span},
    )

    assert parsed.symbol_spans == {"run": span}
