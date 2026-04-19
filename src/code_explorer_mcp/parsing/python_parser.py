from __future__ import annotations

import ast
from dataclasses import dataclass

from code_explorer_mcp.parsing.base import Parser
from code_explorer_mcp.parsing.common import (
    ParsedFile,
    SourcePosition,
    SourceSpan,
    SymbolMatch,
    SymbolSpan,
    make_parsed_file,
    slice_source_span,
)

PYTHON_SYMBOL_TYPES: tuple[str, ...] = (
    "imports",
    "globals",
    "classes",
    "functions",
)


@dataclass(frozen=True, slots=True)
class _ClassParseResult:
    data: dict[str, object]
    symbol_spans: dict[str, SymbolSpan]


class PythonParser(Parser):
    """Parse Python source files using the standard-library ast module only."""

    def supports(self, filename: str) -> bool:
        return filename.endswith(".py")

    def language(self) -> str:
        return "python"

    def available_symbol_types(self) -> list[str]:
        return list(PYTHON_SYMBOL_TYPES)

    def parse_file(self, filename: str, source: str) -> ParsedFile:
        tree = ast.parse(source, filename=filename)
        imports: list[dict[str, str | None]] = []
        globals_section: list[dict[str, str]] = []
        classes: list[dict[str, object]] = []
        functions: list[dict[str, str]] = []
        symbol_spans: dict[str, SymbolSpan] = {}

        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.extend(self._parse_import(node))
                continue

            if isinstance(node, ast.ImportFrom):
                imports.extend(self._parse_import_from(node))
                continue

            if isinstance(node, ast.Assign):
                for name in self._assignment_names(node.targets):
                    globals_section.append({"name": name})
                    symbol_spans[name] = self._make_symbol_span(
                        symbol=name,
                        symbol_type="globals",
                        node=node,
                    )
                continue

            if isinstance(node, ast.AnnAssign):
                for name in self._ann_assign_names(node):
                    globals_section.append({"name": name})
                    symbol_spans[name] = self._make_symbol_span(
                        symbol=name,
                        symbol_type="globals",
                        node=node,
                    )
                continue

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({"name": node.name})
                symbol_spans[node.name] = self._make_symbol_span(
                    symbol=node.name,
                    symbol_type="functions",
                    node=node,
                )
                continue

            if isinstance(node, ast.ClassDef):
                class_result = self._parse_class(
                    node, parent_symbol=None, allow_inner=True
                )
                classes.append(class_result.data)
                symbol_spans.update(class_result.symbol_spans)

        sections = {
            "imports": imports,
            "globals": globals_section,
            "classes": classes,
            "functions": functions,
        }
        return make_parsed_file(
            filename=filename,
            language=self.language(),
            available_symbol_types=self.available_symbol_types(),
            sections=sections,
            symbol_spans=symbol_spans,
        )

    def fetch_symbol(
        self, filename: str, source: str, symbol: str
    ) -> SymbolMatch | None:
        parsed = self.parse_file(filename, source)
        span = parsed.symbol_spans.get(symbol)
        if span is None:
            return None

        return SymbolMatch(
            filename=filename,
            language=self.language(),
            symbol=symbol,
            symbol_type=span.symbol_type,
            code=self._slice_source(source, span.span),
            span=span.span,
        )

    def _parse_import(self, node: ast.Import) -> list[dict[str, str | None]]:
        imports: list[dict[str, str | None]] = []
        for alias in node.names:
            imports.append(
                {
                    "module": alias.name,
                    "name": None,
                    "alias": alias.asname,
                }
            )
        return imports

    def _parse_import_from(self, node: ast.ImportFrom) -> list[dict[str, str | None]]:
        module = "." * node.level + (node.module or "")
        imports: list[dict[str, str | None]] = []
        for alias in node.names:
            imports.append(
                {
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                }
            )
        return imports

    def _parse_class(
        self,
        node: ast.ClassDef,
        *,
        parent_symbol: str | None,
        allow_inner: bool,
    ) -> _ClassParseResult:
        symbol_name = (
            node.name if parent_symbol is None else f"{parent_symbol}.{node.name}"
        )
        members: list[dict[str, str]] = []
        methods: list[dict[str, str]] = []
        inner_classes: list[dict[str, object]] = []
        symbol_spans = {
            symbol_name: self._make_symbol_span(
                symbol=symbol_name,
                symbol_type="classes",
                node=node,
            )
        }

        for child in node.body:
            if isinstance(child, ast.Assign):
                for name in self._assignment_names(child.targets):
                    members.append({"name": name})
                    dotted_name = f"{symbol_name}.{name}"
                    symbol_spans[dotted_name] = self._make_symbol_span(
                        symbol=dotted_name,
                        symbol_type="classes",
                        node=child,
                    )
                continue

            if isinstance(child, ast.AnnAssign):
                for name in self._ann_assign_names(child):
                    members.append({"name": name})
                    dotted_name = f"{symbol_name}.{name}"
                    symbol_spans[dotted_name] = self._make_symbol_span(
                        symbol=dotted_name,
                        symbol_type="classes",
                        node=child,
                    )
                continue

            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({"name": child.name})
                dotted_name = f"{symbol_name}.{child.name}"
                symbol_spans[dotted_name] = self._make_symbol_span(
                    symbol=dotted_name,
                    symbol_type="classes",
                    node=child,
                )
                continue

            if allow_inner and isinstance(child, ast.ClassDef):
                inner_result = self._parse_class(
                    child,
                    parent_symbol=symbol_name,
                    allow_inner=False,
                )
                inner_classes.append(inner_result.data)
                symbol_spans.update(inner_result.symbol_spans)

        return _ClassParseResult(
            data={
                "name": node.name,
                "members": members,
                "methods": methods,
                "inner_classes": inner_classes,
            },
            symbol_spans=symbol_spans,
        )

    def _assignment_names(self, targets: list[ast.expr]) -> list[str]:
        names: list[str] = []
        for target in targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
        return names

    def _ann_assign_names(self, node: ast.AnnAssign) -> list[str]:
        if isinstance(node.target, ast.Name):
            return [node.target.id]
        return []

    def _make_symbol_span(
        self,
        *,
        symbol: str,
        symbol_type: str,
        node: ast.Assign
        | ast.AnnAssign
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.ClassDef,
    ) -> SymbolSpan:
        end_line = node.end_lineno if node.end_lineno is not None else node.lineno
        end_column = (
            node.end_col_offset if node.end_col_offset is not None else node.col_offset
        )
        return SymbolSpan(
            symbol=symbol,
            symbol_type=symbol_type,
            span=SourceSpan(
                start=SourcePosition(
                    line=node.lineno,
                    column=node.col_offset,
                ),
                end=SourcePosition(
                    line=end_line,
                    column=end_column,
                ),
            ),
        )

    def _slice_source(self, source: str, span: SourceSpan) -> str:
        return slice_source_span(
            source,
            span,
            column_to_character_offset=self._character_column_for_utf8_offset,
        )

    def _character_column_for_utf8_offset(self, line_text: str, utf8_offset: int) -> int:
        if utf8_offset < 0:
            raise ValueError(f"Invalid column: {utf8_offset}")
        encoded = line_text.encode("utf-8")
        if utf8_offset > len(encoded):
            raise ValueError(f"Invalid column: {utf8_offset}")
        return len(encoded[:utf8_offset].decode("utf-8"))
