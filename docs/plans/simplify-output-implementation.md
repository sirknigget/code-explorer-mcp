# MCP output narrowing implementation plan

## Context

The goal is to reduce MCP response size and boilerplate for LLM-driven code exploration without changing any existing parsing logic or project-structure discovery logic.

The important constraint is architectural: `get_project_structure`, `parse_file`, and `fetch_symbol` should keep producing the same internal results they produce today. The only change should be a final presentation step that transforms those results into a narrower MCP-visible payload.

That separation matters because the current parser and discovery components already encode the real behavior and invariants of the system. We want to preserve them as-is and make the transport response leaner at the boundary.

## Recommended approach

Add a dedicated MCP presentation layer that sits **after** the existing tool functions and **before** FastMCP serializes the result.

Recommended flow:

1. `src/code_explorer_mcp/server.py` keeps building the same request dataclasses.
2. The existing tool functions stay unchanged:
   - `src/code_explorer_mcp/tool_project_structure.py:get_project_structure`
   - `src/code_explorer_mcp/tool_file_parse.py:parse_file`
   - `src/code_explorer_mcp/tool_symbol_fetch.py:fetch_symbol`
3. Each wrapper in `src/code_explorer_mcp/server.py` passes the returned response dataclass into a new presentation helper.
4. The presentation helper returns the narrowed MCP-facing payload as a plain serializable dict.

This keeps the domain/tool layer stable and moves all output simplification into one explicit transport-only layer.

## Output rules to implement

### `get_project_structure`

Transform the existing `GetProjectStructureResponse` into a compact payload that:

- keeps only the rendered tree and language capability summary
- omits echoed request fields like `root`, `subfolder`, and `pattern`
- omits `languages_present` because that information is redundant once capabilities are present
- renders the tree relative to the requested subfolder when `subfolder` was supplied
- preserves structured errors

Target MCP shape:

```json
{
  "structure": "...",
  "languages": {
    "python": ["imports", "globals", "classes", "functions"],
    "typescript": ["imports", "globals", "classes", "functions", "interfaces", "type_aliases", "enums", "re_exports"]
  }
}
```

### `parse_file`

Transform the existing `ParseFileResponse` into a compact symbol-discovery payload that:

- omits echoed request/context fields like `filename` and `language`
- converts section payloads into arrays of strings
- omits empty and unrequested sections
- keeps `available_symbol_types` only if it is still needed for “full parse” discoverability; otherwise rely on returned section keys
- preserves structured errors

Per-section rules:

- `imports` → compact display strings
- `globals` → symbol names only
- `functions` → names only
- `classes` → flattened qualified names such as `MyClass` and `MyClass.InnerClass`
- `interfaces`, `type_aliases`, `enums` → names only
- `re_exports` → compact display strings
- do **not** include nested member/method/accessor detail in baseline parse output

### `fetch_symbol`

Transform the existing `FetchSymbolResponse` into a code-first payload that:

- always returns `code` on success
- keeps at most `symbol_type` as optional success metadata
- omits echoed request/context fields like `filename`, `language`, and `symbol`
- preserves structured errors

Target MCP shape:

```json
{
  "symbol_type": "interfaces",
  "code": "..."
}
```

## Files to modify

### 1. `src/code_explorer_mcp/server.py`

Update the three FastMCP tool wrappers so they:

- call the existing tool functions exactly as they do now
- immediately pass the internal response dataclass into presentation helpers
- return the narrowed transport payload instead of the raw dataclass

This is the main output boundary and should be the only existing production file where behavior changes.

### 2. `src/code_explorer_mcp/presentation.py` (new)

Create a small pure transformation module with one presenter per tool response:

- `present_project_structure(...)`
- `present_parse_file(...)`
- `present_fetch_symbol(...)`

Responsibilities:

- accept the current response dataclasses from `src/code_explorer_mcp/models.py`
- produce plain serializable dicts
- centralize all output narrowing rules
- preserve error payloads in a deterministic shape
- avoid mutating internal response objects

### 3. `tests/test_mcp_stdio_integration.py`

Update the MCP-facing assertions to match the new narrowed transport contract.

This test should become the canonical assertion for what MCP clients actually receive.

### 4. `tests/test_presentation.py` (new)

Add focused unit tests for the new presentation layer.

Cover:

- successful project-structure transformation
- successful parse transformation for Python and TypeScript sections
- successful symbol fetch transformation
- error passthrough for each tool
- subfolder-relative tree rendering behavior
- flattening of nested classes into qualified names

## Files to keep unchanged

These files should stay behaviorally unchanged:

- `src/code_explorer_mcp/tool_project_structure.py`
- `src/code_explorer_mcp/tool_file_parse.py`
- `src/code_explorer_mcp/tool_symbol_fetch.py`
- `src/code_explorer_mcp/parser_registry.py`
- `src/code_explorer_mcp/parsing/*`
- `src/code_explorer_mcp/utils/tree.py`
- `src/code_explorer_mcp/utils/paths.py`

The plan relies on these remaining the internal source of truth.

## Existing functions and utilities to reuse

Reuse these existing boundaries rather than moving logic upstream:

- `src/code_explorer_mcp/server.py:create_mcp_server`
  - keep this as the MCP transport entrypoint and insert the presentation step here
- `src/code_explorer_mcp/tool_project_structure.py:get_project_structure`
  - continue using it unchanged as the internal structure/discovery result producer
- `src/code_explorer_mcp/tool_file_parse.py:parse_file`
  - continue using it unchanged as the internal parsed-file result producer
- `src/code_explorer_mcp/tool_symbol_fetch.py:fetch_symbol`
  - continue using it unchanged as the internal exact-symbol result producer
- `src/code_explorer_mcp/models.py`
  - keep `GetProjectStructureResponse`, `ParseFileResponse`, `FetchSymbolResponse`, and `ToolPlaceholderError` as the internal response contract consumed by the presenter

Do **not** reimplement parsing, discovery, or path/error logic inside the presentation layer.

## Implementation steps

1. Create `src/code_explorer_mcp/presentation.py` with pure transformation helpers for the three response types.
2. Implement compact conversion helpers for repeated output patterns:
   - compact import string formatting
   - compact re-export string formatting
   - class flattening into qualified names
   - optional omission of empty sections
   - relative tree trimming for `subfolder`
3. Update `src/code_explorer_mcp/server.py` to call these presentation helpers from each MCP wrapper.
4. Keep all direct tool functions returning the same dataclass results as before.
5. Add targeted unit tests for the presentation helpers.
6. Update stdio integration expectations to assert the narrowed MCP output.
7. Keep existing direct-function tests as internal-contract tests unless a test is explicitly transport-facing.

## Verification

### Focused tests

Run the tests that protect both layers:

```bash
uv run pytest tests/test_presentation.py
uv run pytest tests/test_mcp_stdio_integration.py
uv run pytest tests/test_project_structure.py
uv run pytest tests/test_parser_tool_integration.py
uv run pytest tests/test_path_tool_errors.py
```

Why these:

- `tests/test_presentation.py` validates the new transport transformation logic
- `tests/test_mcp_stdio_integration.py` validates actual MCP-visible output
- `tests/test_project_structure.py`, `tests/test_parser_tool_integration.py`, and `tests/test_path_tool_errors.py` confirm the underlying internal logic and error behavior did not change

### Type checking

If return annotations or wrapper signatures change, run:

```bash
uv run pyright
```

### End-to-end MCP check

After tests pass, manually exercise the three tools through the stdio server path and confirm:

- `get_project_structure` returns only compact structure/capability output
- `parse_file` returns string-array sections rather than descriptive structs
- `fetch_symbol` returns mostly code-first output
- invalid-path and symbol-not-found errors remain structured and recoverable

## Key guardrail during implementation

Do not push output simplification backward into:

- parser implementations
- discovery helpers
- direct tool functions

If a simplification can only be achieved by changing those layers, stop and reconsider the presenter design first. The intended architecture here is: **full internal result -> final MCP presentation transform**.