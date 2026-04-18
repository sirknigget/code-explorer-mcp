# Code Explorer MCP MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP FastMCP stdio server that exposes deterministic `get_project_structure`, `parse_file`, and `fetch_symbol` tools for Python and TypeScript/TSX code exploration.

**Architecture:** Add a new `src/code_explorer_mcp` production package with a composition root, explicit response models, project-root-safe path and tree helpers, and a shared parser registry. Implement Python parsing with stdlib `ast`, implement TypeScript parsing through a local `ts-morph` Node bridge, and keep all tool contracts narrow and exact so fixture-driven tests can lock the JSON envelopes and symbol snippets.

**Tech Stack:** Python 3.12, FastMCP, pytest, pytest-asyncio, stdlib `ast`, Node.js, ts-morph, uv

---

## File map

### Production files
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/pyproject.toml` — switch to `src/` package layout, add runtime and test dependencies, add server and TypeScript setup scripts.
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/main.py` — replace POC runner with the real stdio entrypoint.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py` — FastMCP app creation and tool registration.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/models.py` — deterministic response models and helpers.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_project_structure.py` — file discovery, ignore handling, tree rendering, capability discovery.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_file_parse.py` — parser resolution and `content` filtering.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_symbol_fetch.py` — parser resolution and exact snippet fetch.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/base.py` — parser protocol/registry.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/common.py` — shared parsed data structures, spans, symbol matches.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/python_parser.py` — Python parser implementation.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_parser.py` — Python-side wrapper around the Node bridge.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js` — ts-morph bridge executable.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/paths.py` — project-root-aware path normalization and traversal safety.
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/tree.py` — deterministic tree construction and rendering.

### Test and fixture files
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/.gitignore`
- Create fixture tree under `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/` for structure tests.

## Test strategy
- Write exact-output tests first for every contract.
- Use fixture files instead of mocking parser internals.
- Run only the targeted test file(s) after each task.
- Keep negative tests only where FastMCP or parser error envelopes are deterministic enough to assert exactly.

---

### Task 1: Repackage the project as a real `src/` application

**Files:**
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/pyproject.toml`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/main.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py`

- [ ] **Step 1: Write the failing packaging smoke test**

```python
from main import main


def test_main_imports_server_module() -> None:
    try:
        main
    except Exception as exc:  # pragma: no cover
        raise AssertionError(f"main import failed: {exc}") from exc
```

Save it in `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py` temporarily as the first test in the file.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py::test_main_imports_server_module -v`
Expected: FAIL because `src/code_explorer_mcp/server.py` does not exist and `main.py` still points at the POC runner.

- [ ] **Step 3: Update `pyproject.toml` to package the `src/` app**

Replace the current top-level packaging section with this content shape:

```toml
[project]
name = "code-explorer-mcp"
version = "0.1.0"
description = "Local MCP code exploration server"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "fastmcp",
]

[project.optional-dependencies]
test = [
  "pytest",
  "pytest-asyncio",
]

[project.scripts]
code-explorer-mcp = "main:main"
ts-parser-setup = "setup_ts_parser_poc:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Keep `setup_ts_parser_poc.py` as the existing Node bootstrap entrypoint for now; the package layout change is the goal of this task.

- [ ] **Step 4: Replace `main.py` with a thin stdio entrypoint**

```python
from code_explorer_mcp.server import create_app


def main() -> None:
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create the initial server composition root**

```python
from fastmcp import FastMCP


def create_app() -> FastMCP:
    return FastMCP("code-explorer-mcp")
```

Save it to `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py`.

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py::test_main_imports_server_module -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/pyproject.toml /Users/omergilad/workspace/AI/code-explorer-mcp/main.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py
git commit -m "feat: package the MCP server app"
```

---

### Task 2: Define shared parser and response models

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/models.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/base.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/common.py`
- Test: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py`

- [ ] **Step 1: Write the failing model test**

```python
from code_explorer_mcp.parsing.common import ParsedFile, SymbolMatch


def test_parsed_file_model_dump_is_exact() -> None:
    parsed = ParsedFile(
        filename="tests/fixtures/python_sample.py",
        language="python",
        available_symbol_types=["imports", "globals"],
        sections={
            "imports": [{"module": "os", "name": None, "alias": None}],
            "globals": [{"name": "MY_GLOBAL"}],
        },
    )

    assert parsed.to_dict() == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "available_symbol_types": ["imports", "globals"],
        "imports": [{"module": "os", "name": None, "alias": None}],
        "globals": [{"name": "MY_GLOBAL"}],
    }


def test_symbol_match_model_dump_is_exact() -> None:
    match = SymbolMatch(
        filename="tests/fixtures/python_sample.py",
        language="python",
        symbol="MY_GLOBAL",
        symbol_type="globals",
        code="MY_GLOBAL = 1",
    )

    assert match.to_dict() == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "symbol": "MY_GLOBAL",
        "symbol_type": "globals",
        "code": "MY_GLOBAL = 1",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_parsed_file_model_dump_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_symbol_match_model_dump_is_exact -v`
Expected: FAIL because the shared parsing models do not exist.

- [ ] **Step 3: Implement the shared parsing data structures**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/common.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    start_line: int
    end_line: int


@dataclass(frozen=True)
class LocatedSymbol:
    symbol: str
    symbol_type: str
    span: SourceSpan


@dataclass(frozen=True)
class ParsedFile:
    filename: str
    language: str
    available_symbol_types: list[str]
    sections: dict[str, list[dict[str, object]]]
    symbols: dict[str, LocatedSymbol] | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "filename": self.filename,
            "language": self.language,
            "available_symbol_types": self.available_symbol_types,
        }
        result.update(self.sections)
        return result


@dataclass(frozen=True)
class SymbolMatch:
    filename: str
    language: str
    symbol: str
    symbol_type: str
    code: str

    def to_dict(self) -> dict[str, str]:
        return {
            "filename": self.filename,
            "language": self.language,
            "symbol": self.symbol,
            "symbol_type": self.symbol_type,
            "code": self.code,
        }
```

- [ ] **Step 4: Implement the parser interface and registry**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/base.py` with:

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from code_explorer_mcp.parsing.common import ParsedFile, SymbolMatch


class Parser(Protocol):
    def supports(self, filename: str) -> bool: ...
    def language(self) -> str: ...
    def available_symbol_types(self) -> list[str]: ...
    def parse_file(self, filename: str, source: str) -> ParsedFile: ...
    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None: ...


class ParserRegistry:
    def __init__(self, parsers: list[Parser]) -> None:
        self._parsers = parsers

    def for_filename(self, filename: str) -> Parser:
        for parser in self._parsers:
            if parser.supports(filename):
                return parser
        raise ValueError(f"Unsupported file type: {Path(filename).suffix}")

    def capabilities_for_languages_in_files(self, filenames: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for filename in filenames:
            parser = self.for_filename(filename)
            result[parser.language()] = parser.available_symbol_types()
        return dict(sorted(result.items()))
```

- [ ] **Step 5: Add model aliases if the tool layer needs them**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/models.py` with:

```python
from code_explorer_mcp.parsing.common import ParsedFile, SymbolMatch

__all__ = ["ParsedFile", "SymbolMatch"]
```

If you prefer not to use `__all__` because this repo behaves as an application, replace the file with direct imports only and update all imports accordingly.

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_parsed_file_model_dump_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_symbol_match_model_dump_is_exact -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/models.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/base.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/common.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py
git commit -m "feat: add shared parser models"
```

---

### Task 3: Implement project-root-safe path and tree helpers

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/paths.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/tree.py`
- Test: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py`

- [ ] **Step 1: Write the failing helper tests**

```python
from pathlib import Path

from code_explorer_mcp.utils.paths import normalize_relative_path, resolve_within_root
from code_explorer_mcp.utils.tree import render_tree


def test_normalize_relative_path_uses_forward_slashes() -> None:
    assert normalize_relative_path(Path("src") / "pkg" / "file.py") == "src/pkg/file.py"


def test_resolve_within_root_rejects_escape() -> None:
    root = Path("/tmp/project")
    try:
        resolve_within_root(root, "../outside.py")
    except ValueError as exc:
        assert str(exc) == "Path escapes project root: ../outside.py"
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError")


def test_render_tree_is_exact() -> None:
    assert render_tree([
        "src/code_explorer_mcp/server.py",
        "src/code_explorer_mcp/parsing/python_parser.py",
        "tests/fixtures/python_sample.py",
    ]) == (
        "src/\n"
        "  code_explorer_mcp/\n"
        "    parsing/\n"
        "      python_parser.py\n"
        "    server.py\n"
        "tests/\n"
        "  fixtures/\n"
        "    python_sample.py"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_normalize_relative_path_uses_forward_slashes /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_resolve_within_root_rejects_escape /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_render_tree_is_exact -v`
Expected: FAIL because the helper modules do not exist.

- [ ] **Step 3: Implement path helpers**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/paths.py` with:

```python
from __future__ import annotations

from pathlib import Path

IGNORED_DIRECTORIES = {
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}


def project_root() -> Path:
    return Path.cwd().resolve()


def normalize_relative_path(path: Path) -> str:
    return path.as_posix().strip("/")


def resolve_within_root(root: Path, relative_path: str | None) -> Path:
    if not relative_path:
        return root
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {relative_path}") from exc
    return candidate
```

- [ ] **Step 4: Implement deterministic tree rendering**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/tree.py` with:

```python
from __future__ import annotations

from collections import defaultdict


def render_tree(paths: list[str]) -> str:
    tree: dict[str, dict] = {}
    for path in sorted(paths):
        node = tree
        for part in path.split("/"):
            node = node.setdefault(part, {})

    lines: list[str] = []

    def visit(node: dict[str, dict], depth: int) -> None:
        names = sorted(node)
        directories = [name for name in names if node[name]]
        files = [name for name in names if not node[name]]
        for name in directories + files:
            suffix = "/" if node[name] else ""
            lines.append(f"{'  ' * depth}{name}{suffix}")
            if node[name]:
                visit(node[name], depth + 1)

    visit(tree, 0)
    return "\n".join(lines)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_normalize_relative_path_uses_forward_slashes /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_resolve_within_root_rejects_escape /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py::test_render_tree_is_exact -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/paths.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/tree.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py
git commit -m "feat: add path and tree helpers"
```

---

### Task 4: Build fixture files and exact-output tests for Python parsing

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/python_parser.py`

- [ ] **Step 1: Create the Python fixture**

Save this exact fixture to `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py`:

```python
import os
from typing import Any

MY_GLOBAL = 1


class MyClass:
    count = 0

    class InnerClass:
        pass

    def my_method(self) -> str:
        return "ok"


def top_level_function(value: Any) -> Any:
    return value
```

- [ ] **Step 2: Write the failing parser output tests**

```python
from pathlib import Path

from code_explorer_mcp.parsing.python_parser import PythonParser


def test_python_parser_full_output_is_exact() -> None:
    parser = PythonParser()
    source = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py").read_text()

    assert parser.parse_file("tests/fixtures/python_sample.py", source).to_dict() == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "available_symbol_types": ["imports", "globals", "classes", "functions"],
        "imports": [
            {"module": "os", "name": None, "alias": None},
            {"module": "typing", "name": "Any", "alias": None},
        ],
        "globals": [{"name": "MY_GLOBAL"}],
        "classes": [
            {
                "name": "MyClass",
                "members": [{"name": "count"}],
                "methods": [{"name": "my_method"}],
                "inner_classes": [
                    {
                        "name": "InnerClass",
                        "members": [],
                        "methods": [],
                        "inner_classes": [],
                    }
                ],
            }
        ],
        "functions": [{"name": "top_level_function"}],
    }


def test_python_fetch_symbol_returns_exact_snippet() -> None:
    parser = PythonParser()
    source = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py").read_text()

    assert parser.fetch_symbol(
        "tests/fixtures/python_sample.py",
        source,
        "MyClass.my_method",
    ).to_dict() == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "symbol": "MyClass.my_method",
        "symbol_type": "functions",
        "code": '    def my_method(self) -> str:\n        return "ok"',
    }
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_python_parser_full_output_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_python_fetch_symbol_returns_exact_snippet -v`
Expected: FAIL because `PythonParser` does not exist.

- [ ] **Step 4: Implement the Python parser**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/python_parser.py` with these design rules:

```python
from __future__ import annotations

import ast

from code_explorer_mcp.parsing.common import LocatedSymbol, ParsedFile, SourceSpan, SymbolMatch


class PythonParser:
    def supports(self, filename: str) -> bool:
        return filename.endswith(".py")

    def language(self) -> str:
        return "python"

    def available_symbol_types(self) -> list[str]:
        return ["imports", "globals", "classes", "functions"]

    def parse_file(self, filename: str, source: str) -> ParsedFile:
        tree = ast.parse(source)
        lines = source.splitlines()
        imports: list[dict[str, object]] = []
        globals_: list[dict[str, object]] = []
        classes: list[dict[str, object]] = []
        functions: list[dict[str, object]] = []
        symbols: dict[str, LocatedSymbol] = {}
        # Walk only top-level statements.
        # Record spans for globals, classes, first-level inner classes, methods, and top-level functions.
        # Build exact dictionaries matching the tests above.
        return ParsedFile(
            filename=filename,
            language=self.language(),
            available_symbol_types=self.available_symbol_types(),
            sections={
                "imports": imports,
                "globals": globals_,
                "classes": classes,
                "functions": functions,
            },
            symbols=symbols,
        )

    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None:
        parsed = self.parse_file(filename, source)
        match = parsed.symbols.get(symbol) if parsed.symbols else None
        if match is None:
            return None
        code = "\n".join(source.splitlines()[match.span.start_line - 1 : match.span.end_line])
        return SymbolMatch(
            filename=filename,
            language=self.language(),
            symbol=symbol,
            symbol_type=match.symbol_type,
            code=code,
        )
```

While implementing the omitted bodies, follow the spec exactly:
- top-level imports only
- module globals from `Assign` and `AnnAssign`
- top-level classes
- direct class members and methods
- first-level inner classes only
- top-level functions only
- deterministic ordering by source order

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_python_parser_full_output_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_python_fetch_symbol_returns_exact_snippet -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/python_parser.py
git commit -m "feat: add deterministic python parsing"
```

---

### Task 5: Build fixture files and exact-output tests for TypeScript parsing

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_parser.py`
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js`

- [ ] **Step 1: Create the TypeScript fixture**

Save this exact fixture to `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts`:

```ts
import Thing, { Helper } from "./types";

export const TOP_LEVEL_CONST = 1;

export class MyClass {
  value = 1;

  classLike = class InnerClass {};

  get label(): string {
    return "label";
  }

  run(): void {}
}

export function namedFunction(): void {}
export const arrowFunction = (): number => 1;

export interface MyInterface {
  id: string;
}

export type MyType = {
  value: number;
};

export enum MyEnum {
  One = "one",
}

export { SharedThing } from "./shared";
```

- [ ] **Step 2: Write the failing TypeScript parser tests**

```python
from pathlib import Path

from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser


def test_typescript_parser_full_output_is_exact() -> None:
    parser = TypeScriptParser()
    source = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts").read_text()

    assert parser.parse_file("tests/fixtures/typescript_sample.ts", source).to_dict() == {
        "filename": "tests/fixtures/typescript_sample.ts",
        "language": "typescript",
        "available_symbol_types": [
            "imports",
            "globals",
            "classes",
            "functions",
            "interfaces",
            "type_aliases",
            "enums",
            "re_exports",
        ],
        "imports": [{"module": "./types", "default": "Thing", "named": ["Helper"]}],
        "globals": [{"name": "TOP_LEVEL_CONST", "declaration_kind": "const"}],
        "classes": [
            {
                "name": "MyClass",
                "members": [{"name": "value"}],
                "methods": [{"name": "run"}],
                "accessors": [{"name": "label", "kind": "getter"}],
                "inner_classes": [{"name": "InnerClass", "members": [], "methods": [], "accessors": [], "inner_classes": []}],
            }
        ],
        "functions": [
            {"name": "namedFunction", "syntax": "function"},
            {"name": "arrowFunction", "syntax": "arrow"},
        ],
        "interfaces": [{"name": "MyInterface"}],
        "type_aliases": [{"name": "MyType"}],
        "enums": [{"name": "MyEnum"}],
        "re_exports": [{"module": "./shared", "names": ["SharedThing"]}],
    }


def test_typescript_fetch_symbol_returns_exact_snippet() -> None:
    parser = TypeScriptParser()
    source = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts").read_text()

    assert parser.fetch_symbol(
        "tests/fixtures/typescript_sample.ts",
        source,
        "MyInterface",
    ).to_dict() == {
        "filename": "tests/fixtures/typescript_sample.ts",
        "language": "typescript",
        "symbol": "MyInterface",
        "symbol_type": "interfaces",
        "code": "export interface MyInterface {\n  id: string;\n}",
    }
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_typescript_parser_full_output_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_typescript_fetch_symbol_returns_exact_snippet -v`
Expected: FAIL because `TypeScriptParser` does not exist.

- [ ] **Step 4: Implement the Node bridge**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js` with a CLI contract like this:

```javascript
import fs from "node:fs";
import { Project, SyntaxKind } from "ts-morph";

const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const sourceText = payload.source;
const filename = payload.filename;

const project = new Project({ useInMemoryFileSystem: true });
const sourceFile = project.createSourceFile(filename, sourceText, { overwrite: true });

const response = {
  filename,
  language: "typescript",
  available_symbol_types: [
    "imports",
    "globals",
    "classes",
    "functions",
    "interfaces",
    "type_aliases",
    "enums",
    "re_exports",
  ],
  sections: {
    imports: [],
    globals: [],
    classes: [],
    functions: [],
    interfaces: [],
    type_aliases: [],
    enums: [],
    re_exports: [],
  },
  symbols: {},
};

// Fill each section deterministically from the ts-morph AST.
// Use sourceFile.getFullText().split(/\r?\n/) only if exact line slicing is needed.
// Record spans keyed by symbol names like "MyClass", "MyClass.run", "MyInterface", "arrowFunction".

process.stdout.write(JSON.stringify(response));
```

Reuse the existing POC ideas from `/Users/omergilad/workspace/AI/code-explorer-mcp/src/ts_parser_poc`, but do not import from `src/legacy`.

- [ ] **Step 5: Implement the Python wrapper parser**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_parser.py` with this structure:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_explorer_mcp.parsing.common import LocatedSymbol, ParsedFile, SourceSpan, SymbolMatch


class TypeScriptParser:
    def supports(self, filename: str) -> bool:
        return filename.endswith(".ts") or filename.endswith(".tsx")

    def language(self) -> str:
        return "typescript"

    def available_symbol_types(self) -> list[str]:
        return [
            "imports",
            "globals",
            "classes",
            "functions",
            "interfaces",
            "type_aliases",
            "enums",
            "re_exports",
        ]

    def parse_file(self, filename: str, source: str) -> ParsedFile:
        bridge_path = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js")
        completed = subprocess.run(
            ["node", str(bridge_path)],
            input=json.dumps({"filename": filename, "source": source}),
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        symbols = {
            key: LocatedSymbol(
                symbol=key,
                symbol_type=value["symbol_type"],
                span=SourceSpan(
                    start_line=value["start_line"],
                    end_line=value["end_line"],
                ),
            )
            for key, value in payload["symbols"].items()
        }
        return ParsedFile(
            filename=payload["filename"],
            language=payload["language"],
            available_symbol_types=payload["available_symbol_types"],
            sections=payload["sections"],
            symbols=symbols,
        )

    def fetch_symbol(self, filename: str, source: str, symbol: str) -> SymbolMatch | None:
        parsed = self.parse_file(filename, source)
        match = parsed.symbols.get(symbol) if parsed.symbols else None
        if match is None:
            return None
        code = "\n".join(source.splitlines()[match.span.start_line - 1 : match.span.end_line])
        return SymbolMatch(
            filename=filename,
            language=self.language(),
            symbol=symbol,
            symbol_type=match.symbol_type,
            code=code,
        )
```

- [ ] **Step 6: Run the Node setup command once**

Run: `uv run ts-parser-setup`
Expected: PASS and Node dependencies are installed for the bridge runtime.

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_typescript_parser_full_output_is_exact /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_typescript_fetch_symbol_returns_exact_snippet -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_parser.py /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js
git commit -m "feat: add deterministic typescript parsing"
```

---

### Task 6: Implement `parse_file` tool routing and content filtering

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_file_parse.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py`

- [ ] **Step 1: Write the failing tool-level filtering tests**

Add exact tests like these:

```python
from pathlib import Path

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.parsing.python_parser import PythonParser
from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser
from code_explorer_mcp.tool_file_parse import parse_file_tool


def test_parse_file_filters_python_sections_exactly() -> None:
    result = parse_file_tool(
        registry=ParserRegistry([PythonParser(), TypeScriptParser()]),
        filename="tests/fixtures/python_sample.py",
        content={"functions": True, "classes": False},
        source_text=Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py").read_text(),
    )

    assert result == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "available_symbol_types": ["imports", "globals", "classes", "functions"],
        "functions": [{"name": "top_level_function"}],
    }
```

```python

def test_parse_file_rejects_unknown_typescript_section() -> None:
    try:
        parse_file_tool(
            registry=ParserRegistry([PythonParser(), TypeScriptParser()]),
            filename="tests/fixtures/typescript_sample.ts",
            content={"made_up": True},
            source_text=Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts").read_text(),
        )
    except ValueError as exc:
        assert str(exc) == "Unknown content filter for typescript: made_up"
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_parse_file_filters_python_sections_exactly /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_parse_file_rejects_unknown_typescript_section -v`
Expected: FAIL because the tool module does not exist.

- [ ] **Step 3: Implement `parse_file_tool`**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_file_parse.py` with:

```python
from __future__ import annotations

from pathlib import Path

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.utils.paths import normalize_relative_path, project_root, resolve_within_root


def parse_file_tool(
    *,
    registry: ParserRegistry,
    filename: str,
    content: dict[str, bool] | None,
    source_text: str | None = None,
) -> dict[str, object]:
    root = project_root()
    file_path = resolve_within_root(root, filename)
    parser = registry.for_filename(filename)
    source = source_text if source_text is not None else file_path.read_text()
    parsed = parser.parse_file(normalize_relative_path(file_path.relative_to(root)), source)

    if content is None:
        return parsed.to_dict()

    requested = [key for key, enabled in content.items() if enabled]
    for key in requested:
        if key not in parsed.available_symbol_types:
            raise ValueError(f"Unknown content filter for {parsed.language}: {key}")

    result: dict[str, object] = {
        "filename": parsed.filename,
        "language": parsed.language,
        "available_symbol_types": parsed.available_symbol_types,
    }
    for key in requested:
        result[key] = parsed.sections[key]
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py::test_parse_file_filters_python_sections_exactly /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py::test_parse_file_rejects_unknown_typescript_section -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_file_parse.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py
git commit -m "feat: add parse file tool filtering"
```

---

### Task 7: Implement `fetch_symbol` with exact source slicing

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_symbol_fetch.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py`

- [ ] **Step 1: Write the failing fetch tests**

Add exact tests for these symbol forms:

```python
from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.parsing.python_parser import PythonParser
from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol_tool


def test_fetch_symbol_python_global_exact() -> None:
    result = fetch_symbol_tool(
        registry=ParserRegistry([PythonParser(), TypeScriptParser()]),
        filename="tests/fixtures/python_sample.py",
        symbol="MY_GLOBAL",
    )

    assert result == {
        "filename": "tests/fixtures/python_sample.py",
        "language": "python",
        "symbol": "MY_GLOBAL",
        "symbol_type": "globals",
        "code": "MY_GLOBAL = 1",
    }
```

```python

def test_fetch_symbol_typescript_interface_exact() -> None:
    result = fetch_symbol_tool(
        registry=ParserRegistry([PythonParser(), TypeScriptParser()]),
        filename="tests/fixtures/typescript_sample.ts",
        symbol="MyInterface",
    )

    assert result == {
        "filename": "tests/fixtures/typescript_sample.ts",
        "language": "typescript",
        "symbol": "MyInterface",
        "symbol_type": "interfaces",
        "code": "export interface MyInterface {\n  id: string;\n}",
    }
```

Also add exact tests for `top_level_function`, `MyClass`, `MyClass.my_method`, `MyClass.InnerClass`, `MyType`, `MyEnum`, `arrowFunction`, and `MyClass.label`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py -v`
Expected: FAIL because the tool module does not exist.

- [ ] **Step 3: Implement `fetch_symbol_tool`**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_symbol_fetch.py` with:

```python
from __future__ import annotations

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.utils.paths import normalize_relative_path, project_root, resolve_within_root


def fetch_symbol_tool(*, registry: ParserRegistry, filename: str, symbol: str) -> dict[str, object]:
    root = project_root()
    file_path = resolve_within_root(root, filename)
    parser = registry.for_filename(filename)
    source = file_path.read_text()
    relative_filename = normalize_relative_path(file_path.relative_to(root))
    match = parser.fetch_symbol(relative_filename, source, symbol)
    if match is None:
        raise ValueError(f"Symbol not found: {symbol}")
    return match.to_dict()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_symbol_fetch.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py
git commit -m "feat: add fetch symbol tool"
```

---

### Task 8: Implement `get_project_structure` with ignore rules and capability discovery

**Files:**
- Create: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_project_structure.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py`
- Create fixture tree under `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/`

- [ ] **Step 1: Create the tree fixture layout**

Create these fixture files:

```text
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/.gitignore
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/src/app.py
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/src/lib/util.ts
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/notes.txt
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/build/generated.py
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/node_modules/pkg/index.js
/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/ignored/secret.py
```

Use this `.gitignore` content:

```gitignore
ignored/
```

- [ ] **Step 2: Write the failing structure tests**

Add exact tests like these:

```python
from pathlib import Path

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.parsing.python_parser import PythonParser
from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser
from code_explorer_mcp.tool_project_structure import get_project_structure_tool


def test_get_project_structure_full_output_is_exact(tmp_path: Path) -> None:
    fixture_root = Path("/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture")

    result = get_project_structure_tool(
        root=fixture_root,
        registry=ParserRegistry([PythonParser(), TypeScriptParser()]),
        subfolder=None,
        pattern=None,
    )

    assert result == {
        "root": ".",
        "subfolder": None,
        "pattern": None,
        "structure": "notes.txt\nsrc/\n  app.py\n  lib/\n    util.ts",
        "languages_present": ["python", "typescript"],
        "available_symbol_types_by_language": {
            "python": ["imports", "globals", "classes", "functions"],
            "typescript": [
                "imports",
                "globals",
                "classes",
                "functions",
                "interfaces",
                "type_aliases",
                "enums",
                "re_exports",
            ],
        },
    }
```

Add exact tests for:
- `subfolder="src"`
- `pattern="*.py"`
- `pattern="*.py,*.ts"`
- folder wildcard behavior such as `pattern="src/*"`
- ignored generated directories and `.gitignore` exclusions

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py -v`
Expected: FAIL because the tool module does not exist.

- [ ] **Step 4: Implement `get_project_structure_tool`**

Create `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_project_structure.py` with these responsibilities:

```python
from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.utils.paths import IGNORED_DIRECTORIES, normalize_relative_path, resolve_within_root
from code_explorer_mcp.utils.tree import render_tree


def get_project_structure_tool(
    *,
    root: Path,
    registry: ParserRegistry,
    subfolder: str | None,
    pattern: str | None,
) -> dict[str, object]:
    start = resolve_within_root(root.resolve(), subfolder)
    patterns = [item.strip() for item in pattern.split(",")] if pattern else []
    files: list[str] = []

    for path in sorted(start.rglob("*")):
        if path.is_dir() and path.name in IGNORED_DIRECTORIES:
            continue
        if not path.is_file():
            continue
        relative_path = normalize_relative_path(path.relative_to(root))
        # Skip .gitignore-matched files.
        # Apply comma-separated wildcard patterns against the normalized relative path.
        files.append(relative_path)

    capabilities = registry.capabilities_for_languages_in_files(files)
    return {
        "root": ".",
        "subfolder": subfolder,
        "pattern": pattern,
        "structure": render_tree(files),
        "languages_present": sorted(capabilities),
        "available_symbol_types_by_language": capabilities,
    }
```

When filling the omitted logic:
- apply patterns to project-relative paths, not absolute paths
- skip ignored directories even if they appear during recursive walking
- honor the root `.gitignore` in the selected tree root
- return deterministic directory-before-file ordering

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_project_structure.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture
git commit -m "feat: add project structure discovery"
```

---

### Task 9: Wire the three tools into the FastMCP server

**Files:**
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py`
- Modify: `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py`

- [ ] **Step 1: Write the failing integration tests**

Add async integration tests that:
- start the server through the local Python entrypoint
- call `list_tools()` and assert exact names
- invoke all three tools with fixture inputs and assert exact JSON results

Use the FastMCP client API available in the installed package. The core shape should be:

```python
import asyncio
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_mcp_server_lists_expected_tools() -> None:
    ...
```

Exact assertions required:
- tool names are `get_project_structure`, `parse_file`, `fetch_symbol`
- `get_project_structure` returns both `languages_present` and `available_symbol_types_by_language`
- `parse_file` can request a language-specific subset
- `fetch_symbol` returns the exact snippet for `MyInterface`

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py -v`
Expected: FAIL because `server.py` does not yet register the tools.

- [ ] **Step 3: Implement the server wiring**

Update `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py` to:
- instantiate `FastMCP("code-explorer-mcp")`
- instantiate a shared `ParserRegistry([PythonParser(), TypeScriptParser()])`
- register three tools named exactly `get_project_structure`, `parse_file`, `fetch_symbol`
- keep each tool as a thin wrapper over the dedicated tool modules

Implementation shape:

```python
from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.parsing.python_parser import PythonParser
from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser
from code_explorer_mcp.tool_file_parse import parse_file_tool
from code_explorer_mcp.tool_project_structure import get_project_structure_tool
from code_explorer_mcp.tool_symbol_fetch import fetch_symbol_tool
from code_explorer_mcp.utils.paths import project_root


def create_app() -> FastMCP:
    app = FastMCP("code-explorer-mcp")
    registry = ParserRegistry([PythonParser(), TypeScriptParser()])

    @app.tool
    def get_project_structure(subfolder: str | None = None, pattern: str | None = None) -> dict[str, object]:
        return get_project_structure_tool(
            root=project_root(),
            registry=registry,
            subfolder=subfolder,
            pattern=pattern,
        )

    @app.tool
    def parse_file(filename: str, content: dict[str, bool] | None = None) -> dict[str, object]:
        return parse_file_tool(registry=registry, filename=filename, content=content)

    @app.tool
    def fetch_symbol(filename: str, symbol: str) -> dict[str, object]:
        return fetch_symbol_tool(registry=registry, filename=filename, symbol=symbol)

    return app
```

- [ ] **Step 4: Run the integration tests to verify they pass**

Run: `uv run pytest /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py
git commit -m "feat: expose MCP tool contracts"
```

---

### Task 10: Run full MVP verification and tighten deterministic failures

**Files:**
- Modify as needed: the production and test files above

- [ ] **Step 1: Run the focused MVP test set**

Run:

```bash
uv run pytest \
  /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py \
  /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py \
  /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py \
  /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py \
  /Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py -v
```

Expected: PASS for all tests.

- [ ] **Step 2: Manually verify stdio behavior once**

Run a one-off client or direct server launch using the local entrypoint and confirm:
- the server starts without importing `src/legacy`
- `list_tools()` reports the three expected tools
- each tool returns normalized relative paths and deterministic ordering

- [ ] **Step 3: Add exact negative tests only where outputs are stable**

If the real error shapes are deterministic, add exact tests for:
- unsupported file type in `parse_file`
- unsupported content filter in `parse_file`
- missing symbol in `fetch_symbol`

Do not add substring assertions; use exact equality for the message or exact exception string.

- [ ] **Step 4: Re-run only the affected test files**

Run the specific pytest modules that changed in Step 3.
Expected: PASS

- [ ] **Step 5: Review the diff for security and scope**

Check:
- no secrets or tokens were added
- no imports from `/Users/omergilad/workspace/AI/code-explorer-mcp/src/legacy`
- no path traversal outside the project root
- no broad extra features outside the MVP spec

- [ ] **Step 6: Commit**

```bash
git add /Users/omergilad/workspace/AI/code-explorer-mcp/pyproject.toml /Users/omergilad/workspace/AI/code-explorer-mcp/main.py /Users/omergilad/workspace/AI/code-explorer-mcp/src /Users/omergilad/workspace/AI/code-explorer-mcp/tests
git commit -m "test: verify deterministic MCP MVP behavior"
```

---

## Spec coverage check
- FastMCP stdio entrypoint: Task 1 and Task 9
- Shared parser abstraction and registry: Task 2
- Path normalization and traversal protection: Task 3
- Python parsing contract: Task 4
- TypeScript/TSX parsing via `ts-morph`: Task 5
- `parse_file` content filtering: Task 6
- `fetch_symbol` exact snippet contract: Task 7
- `get_project_structure` capability-first discovery: Task 8
- MCP integration and exact tool list: Task 9
- Final verification and deterministic negative tests: Task 10

## Placeholder scan
- No `TODO`, `TBD`, or “similar to previous task” placeholders remain.
- Where implementation details are intentionally omitted, the omitted body is tightly constrained by exact tests in the same task.

## Type consistency check
- Shared parser interface methods are consistent across Tasks 2, 4, 5, 6, 7, and 9.
- Tool names are consistently `get_project_structure`, `parse_file`, and `fetch_symbol`.
- Supported section names remain aligned with the spec for Python and TypeScript.
