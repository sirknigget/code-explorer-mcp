# Project Review Report

Date: 2026-04-18
Repository: `code-explorer-mcp`
Scope: Static review of source and tests only; no runtime validation performed.

## 1. Issues / potential bugs

### 1.1 Unicode-related source slicing can return incorrect symbol code
- **Files:** `src/code_explorer_mcp/parsing/python_parser.py:236`, `src/code_explorer_mcp/parsing/python_parser.py:266`, `src/code_explorer_mcp/parsing/typescript_bridge.mjs:14`, `src/code_explorer_mcp/parsing/typescript_parser.py:128`
- **What looks wrong:** Both parsers build source spans from parser-provided line/column positions and then slice Python strings directly using those offsets.
- **Why this is risky:** Parser offsets are not guaranteed to align with Python string indexing for all Unicode cases. In practice, files containing non-ASCII or non-BMP characters can cause `fetch_symbol` to return truncated or shifted code.
- **Impact:** Incorrect `fetch_symbol` results for valid source files.
- **Recommendation:** Add explicit Unicode fixture coverage and normalize span handling so offsets are computed in the same representation on both ends.

### 1.2 File I/O failures are not converted into tool-level errors
- **Files:** `src/code_explorer_mcp/tool_file_parse.py:17`, `src/code_explorer_mcp/tool_symbol_fetch.py:15`
- **What looks wrong:** These tools handle `ProjectPathError` and `ValueError`, but not `UnicodeDecodeError`, `PermissionError`, `IsADirectoryError`, or general `OSError` from `read_text()`.
- **Why this is risky:** A malformed, binary, unreadable, or permission-restricted file will likely surface as an unstructured server failure instead of a clean MCP response.
- **Impact:** Reduced robustness against real-world repositories.
- **Recommendation:** Catch expected file-read exceptions and return structured `ToolPlaceholderError` responses.

### 1.3 Nested Python classes deeper than one level are silently ignored
- **File:** `src/code_explorer_mcp/parsing/python_parser.py:205`
- **What looks wrong:** `_parse_class()` only recurses into inner classes when `allow_inner` is true, and then forces the next level to `False`.
- **Why this is risky:** Deeper nested class symbols exist in valid Python code but will never be reported or fetchable.
- **Impact:** Incomplete parsing/fetch behavior for legitimate code structures.
- **Recommendation:** Recurse without an arbitrary depth cutoff unless there is a documented product requirement not to.

### 1.4 Absolute paths are silently rewritten during normalization
- **File:** `src/code_explorer_mcp/utils/paths.py:30`
- **What looks wrong:** `normalize_relative_path()` strips empty path segments, so an absolute path like `/tmp/x.py` becomes `tmp/x.py`.
- **Why this is risky:** This can hide caller mistakes and produce misleading normalized results that look project-relative when they were not.
- **Impact:** Confusing behavior and weaker path validation semantics.
- **Recommendation:** Reject absolute inputs in the relative-path normalizer instead of coercing them.

### 1.5 `.gitignore` support is incomplete compared with actual Git behavior
- **Files:** `src/code_explorer_mcp/tool_project_structure.py:73`, `src/code_explorer_mcp/tool_project_structure.py:128`
- **What looks wrong:** Only the root `.gitignore` is read; negation rules (`!`) are skipped entirely; matching is a simplified custom approximation.
- **Why this is risky:** Results from `get_project_structure` can diverge from what users expect based on Git.
- **Impact:** Files may appear when they should be hidden, or vice versa, especially in repos with nested `.gitignore` files or exceptions.
- **Recommendation:** Either document the supported subset clearly or adopt a more faithful gitignore matcher.

### 1.6 Global runtime root introduces mutable shared state
- **File:** `src/code_explorer_mcp/runtime_context.py:5`
- **What looks wrong:** Runtime root is stored in a module-global variable.
- **Why this is risky:** Mutable global configuration is fragile in tests and can become problematic if the server is ever used in a more concurrent or re-entrant way.
- **Impact:** Harder-to-reason-about behavior and potential cross-test contamination.
- **Recommendation:** Keep configuration at the composition root and pass it explicitly into tool wiring where possible.

## 2. Code smells / bad practices / suspicious areas

### 2.1 Vendoring `node_modules` inside source is heavy and brittle
- **Files:** `src/code_explorer_mcp/parsing/node_modules/`, `src/setup_node_runtime.py:22`
- **What looks wrong:** The repository includes the Node dependency tree under `src/code_explorer_mcp/parsing/node_modules` and also provides an install step.
- **Why it seems off:** Vendored runtime dependencies increase repository weight, complicate updates, and blur the contract between checked-in assets and generated setup state.
- **Recommendation:** Prefer a cleaner install/setup boundary unless offline vendoring is an explicit requirement.

### 2.2 Test coverage misses the most failure-prone edges
- **Files:** `tests/test_parser_tool_integration.py:20`, `tests/test_project_structure.py:41`, `tests/test_parsing_foundation.py:56`
- **What looks wrong:** The suite covers happy paths well, but there is no visible coverage for:
  - Unicode symbol extraction
  - unreadable/binary file handling
  - deep nested Python classes
  - `.gitignore` negation/nested rules
  - path normalization with absolute inputs
- **Why it matters:** These are the areas where the current implementation looks most fragile.
- **Recommendation:** Add focused regression tests for these boundaries.

### 2.3 Parser symbol types mix structural categories in a surprising way
- **File:** `src/code_explorer_mcp/parsing/python_parser.py:177`, `src/code_explorer_mcp/parsing/python_parser.py:198`
- **What looks wrong:** Class members and methods are stored under symbol type `classes` rather than a more specific category.
- **Why it seems off:** This may be intentional, but it makes the meaning of `symbol_type` less precise and could be confusing for downstream consumers.
- **Recommendation:** Clarify the API contract or consider a more explicit classification model.

### 2.4 Setup script validates tool presence but not dependency health
- **File:** `src/setup_node_runtime.py:12`
- **What looks wrong:** `ensure_node_runtime()` only checks that `node` and `npm` exist; installation success is delegated entirely to `npm install`.
- **Why it seems off:** This is not a bug by itself, but the setup path gives limited diagnostics and no verification that the expected packages for the TypeScript bridge are actually available after install.
- **Recommendation:** Consider a lightweight post-install validation that the bridge can load the required packages.

### 2.5 Root-level test setup mutates global runtime state during import
- **File:** `tests/test_parser_tool_integration.py:17`
- **What looks wrong:** `configure_runtime_root(...)` is called at import time.
- **Why it seems off:** Import-time global mutation makes tests more order-sensitive and less isolated than fixture-based setup.
- **Recommendation:** Move runtime-root setup into fixtures or individual tests.

## 3. Overall assessment

The project is small, readable, and fairly well-scoped. The biggest concerns are correctness around source spans, incomplete error handling for file reads, and a few contract mismatches between the intended behavior and what the current implementation likely does in edge cases. The test suite is solid on the main path, but it does not currently protect the most fragile boundaries.

## 4. Suggested priority order

1. Fix and test Unicode-safe symbol slicing.
2. Add structured handling for file read/decode errors.
3. Remove the arbitrary nested-class depth limit or document it explicitly.
4. Tighten path normalization semantics for absolute paths.
5. Decide whether `.gitignore` behavior should be approximate or Git-faithful, then align implementation/tests accordingly.
