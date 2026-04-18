from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from code_explorer_mcp.parsing.common import ParsedFile, ParserCapabilities, SymbolMatch, make_capabilities


class Parser(ABC):
    """Shared abstraction for language-specific file parsers."""

    @abstractmethod
    def supports(self, filename: str) -> bool:
        """Return whether this parser handles filename."""

    @abstractmethod
    def language(self) -> str:
        """Return the parser language identifier."""

    @abstractmethod
    def available_symbol_types(self) -> list[str]:
        """Return supported top-level symbol section names."""

    @abstractmethod
    def parse_file(self, filename: str, source: str) -> ParsedFile:
        """Parse a source file into a deterministic result envelope."""

    @abstractmethod
    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None:
        """Return an exact symbol match or None."""

    def capabilities(self) -> ParserCapabilities:
        return make_capabilities(self.language(), self.available_symbol_types())


class ParserRegistry:
    """Register parsers and resolve them by filename or language."""

    def __init__(self, parsers: list[Parser] | None = None) -> None:
        self._parsers: list[Parser] = []
        self._parsers_by_language: dict[str, Parser] = {}

        for parser in parsers or []:
            self.register(parser)

    def register(self, parser: Parser) -> None:
        language = parser.language()
        if language in self._parsers_by_language:
            raise ValueError(f"Parser already registered for language: {language}")

        self._parsers.append(parser)
        self._parsers_by_language[language] = parser

    def list_languages(self) -> list[str]:
        return sorted(self._parsers_by_language)

    def list_capabilities(self) -> dict[str, list[str]]:
        return {
            parser.language(): list(parser.available_symbol_types())
            for parser in sorted(self._parsers, key=lambda item: item.language())
        }

    def get_by_language(self, language: str) -> Parser:
        try:
            return self._parsers_by_language[language]
        except KeyError as exc:
            raise ValueError(f"No parser registered for language: {language}") from exc

    def get_for_filename(self, filename: str | Path) -> Parser:
        normalized = str(filename)
        for parser in self._parsers:
            if parser.supports(normalized):
                return parser
        raise ValueError(f"No parser registered for file: {filename}")

    def capabilities_for_paths(self, relative_paths: list[str]) -> dict[str, list[str]]:
        """Return capabilities only for languages present in the given paths."""
        present_languages: dict[str, list[str]] = {}
        for relative_path in relative_paths:
            try:
                parser = self.get_for_filename(relative_path)
            except ValueError:
                continue
            present_languages.setdefault(
                parser.language(),
                list(parser.available_symbol_types()),
            )
        return dict(sorted(present_languages.items()))
