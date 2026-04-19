# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development commands

- Initial setup:
  - `uv sync --extra test`
  - `uv run node-setup`
- Run the MCP server:
  - `uv run code-explorer-mcp`
- Run all tests:
  - `uv run pytest`
- Run one test module:
  - `uv run pytest tests/test_parser_tool_integration.py`
- Run one test case:
  - `uv run pytest tests/test_parser_tool_integration.py::test_fetch_symbol_returns_symbol_not_found_error`

## Architecture overview

This repository is a local FastMCP server that exposes deterministic code-exploration tools for Python and TypeScript repositories.

### Request flow

- The CLI entrypoint is `src/code_explorer_mcp/main.py`; it only boots the FastMCP server.
- `src/code_explorer_mcp/server.py` is the composition root. It registers the three MCP tools and translates tool arguments into typed request/response dataclasses from `src/code_explorer_mcp/models.py`.
- Tool implementation lives in:
  - `src/code_explorer_mcp/tool_project_structure.py`
  - `src/code_explorer_mcp/tool_file_parse.py`
  - `src/code_explorer_mcp/tool_symbol_fetch.py`

### Core tool boundaries

- `get_project_structure` walks the current working directory, applies `.gitignore` plus a built-in ignored-directory list, then renders a deterministic tree and reports which parser capabilities are available for the matched files.
- `parse_file` resolves a project-relative path safely, selects a parser by filename extension, parses the file, and returns only the requested symbol sections when `content` is provided.
- `fetch_symbol` uses the same parser registry and safe path resolution, then slices the exact source span for a named symbol.

### Parser design

- Language support is plugin-style through `Parser` and `ParserRegistry` in `src/code_explorer_mcp/parsing/base.py`.
- `src/code_explorer_mcp/parser_registry.py` wires the default registry with the Python and TypeScript parsers.
- Python parsing is pure stdlib AST in `src/code_explorer_mcp/parsing/python_parser.py`.
- Python and TypeScript class parsing intentionally expose nested classes only one level deep: a top-level class may report direct `inner_classes`, while deeper nested classes are ignored.
- TypeScript parsing is delegated to a Node bridge in `src/code_explorer_mcp/parsing/typescript_parser.py`, which shells out to `typescript_bridge.mjs` and requires Node dependencies installed under `src/code_explorer_mcp/parsing/node_modules`.
- Shared parsed-file and source-span structures live in `src/code_explorer_mcp/parsing/common.py`; they are what keeps responses deterministic across parsers.

### Path and tree invariants

- Path validation is centralized in `src/code_explorer_mcp/utils/paths.py`; tool code should use these helpers instead of custom path joining so requests cannot escape the project root.
- Tree rendering is centralized in `src/code_explorer_mcp/utils/tree.py`; structure output is expected to stay deterministic and sorted.

### Tests

- `tests/test_parser_tool_integration.py` is the main contract test for parser selection, section filtering, and exact symbol extraction.
- `tests/test_mcp_stdio_integration.py` exercises the real stdio FastMCP server end to end.
- The remaining test modules cover path normalization, tree rendering, parser foundation behavior, and project-structure filtering.

## Working notes

- For new language support, add a new `Parser` implementation and register it in `src/code_explorer_mcp/parser_registry.py`; the MCP tools should not need language-specific branching.
