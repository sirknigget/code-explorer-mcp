from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from code_explorer_mcp.parsing.base import Parser
from code_explorer_mcp.parsing.common import (
    ParsedFile,
    SourcePosition,
    SourceSpan,
    SymbolMatch,
    SymbolSpan,
    make_parsed_file,
)

TYPESCRIPT_SYMBOL_TYPES: tuple[str, ...] = (
    "imports",
    "globals",
    "classes",
    "functions",
    "interfaces",
    "type_aliases",
    "enums",
    "re_exports",
)

PARSER_ROOT = Path(__file__).resolve().parent
BRIDGE_PATH = PARSER_ROOT / "typescript_bridge.mjs"
NODE_MODULES = PARSER_ROOT / "node_modules"


class TypeScriptParser(Parser):
    def supports(self, filename: str) -> bool:
        lowered = filename.lower()
        return lowered.endswith(".ts") or lowered.endswith(".tsx")

    def language(self) -> str:
        return "typescript"

    def available_symbol_types(self) -> list[str]:
        return list(TYPESCRIPT_SYMBOL_TYPES)

    def parse_file(self, filename: str, source: str) -> ParsedFile:
        payload = self._run_bridge(filename=filename, source=source)
        sections = {
            symbol_type: payload[symbol_type]
            for symbol_type in TYPESCRIPT_SYMBOL_TYPES
            if symbol_type in payload
        }
        return make_parsed_file(
            filename=filename,
            language=self.language(),
            available_symbol_types=TYPESCRIPT_SYMBOL_TYPES,
            sections=sections,
            symbol_spans=self._load_symbol_spans(payload.get("symbol_spans", {})),
        )

    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None:
        parsed = self.parse_file(filename=filename, source=source)
        symbol_span = parsed.symbol_spans.get(symbol)
        if symbol_span is None:
            return None
        return SymbolMatch(
            filename=filename,
            language=self.language(),
            symbol=symbol,
            symbol_type=symbol_span.symbol_type,
            code=self._slice_source(source, symbol_span.span),
            span=symbol_span.span,
        )

    def _run_bridge(self, *, filename: str, source: str) -> dict[str, Any]:
        self._ensure_ready()
        completed = subprocess.run(
            ["node", str(BRIDGE_PATH)],
            check=True,
            text=True,
            capture_output=True,
            input=json.dumps({"filename": filename, "source": source}),
            cwd=NODE_MODULES.parent,
        )
        if not completed.stdout:
            raise RuntimeError(completed.stderr or "TypeScript bridge produced no output")
        return json.loads(completed.stdout)

    def _ensure_ready(self) -> None:
        if not shutil.which("node"):
            raise RuntimeError(
                "Node.js is required for TypeScript parsing. "
                "Install Node.js, run `uv run code-explorer-mcp-node-setup`, then rerun the parser."
            )
        if not NODE_MODULES.exists():
            raise RuntimeError(
                "TypeScript parser dependencies are not installed. "
                "Run `uv run code-explorer-mcp-node-setup` after `uv sync`, then rerun the parser."
            )

    def _load_symbol_spans(
        self,
        raw_symbol_spans: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, SymbolSpan]:
        symbol_spans: dict[str, SymbolSpan] = {}
        for symbol, payload in raw_symbol_spans.items():
            symbol_spans[symbol] = SymbolSpan(
                symbol=symbol,
                symbol_type=str(payload["symbol_type"]),
                span=self._load_span(payload["span"]),
            )
        return symbol_spans

    def _load_span(self, payload: Mapping[str, Any]) -> SourceSpan:
        start_payload = payload["start"]
        end_payload = payload["end"]
        return SourceSpan(
            start=SourcePosition(
                line=int(start_payload["line"]),
                column=int(start_payload["column"]),
            ),
            end=SourcePosition(
                line=int(end_payload["line"]),
                column=int(end_payload["column"]),
            ),
        )

    def _slice_source(self, source: str, span: SourceSpan) -> str:
        lines = source.splitlines(keepends=True)
        start_offset = self._offset_for_position(lines, span.start)
        end_offset = self._offset_for_position(lines, span.end)
        return source[start_offset:end_offset]

    def _offset_for_position(
        self,
        lines: list[str],
        position: SourcePosition,
    ) -> int:
        if position.line < 1:
            raise ValueError(f"Invalid line number: {position.line}")
        if position.line > len(lines):
            return sum(len(line) for line in lines)

        offset = sum(len(line) for line in lines[: position.line - 1])
        line_text = lines[position.line - 1]
        if position.column < 0 or position.column > len(line_text):
            raise ValueError(
                f"Invalid column {position.column} for line {position.line}",
            )
        return offset + position.column
