# Context
This project’s general purpose is to provide a local FastMCP server that gives coding agents deterministic codebase-exploration primitives for working inside a repository. The server should help clients discover the project layout, understand supported source-file symbols, parse individual files into stable structured output, and fetch exact source code for named symbols.

This document describes the MVP only. The MVP should optimize for stable contracts, exact-output tests, deterministic ordering, and simple local usage over maximum language coverage or deep semantic analysis.

The MVP should initially support:
- Python parsing via stdlib `ast`
- TypeScript and TSX parsing via an existing parser implementation

The design must leave room to add more languages later, but language support should stay behind a shared parser abstraction. The abstraction should unify parser discovery, capability reporting, parsing, and symbol fetching. It should not force every language into the same symbol taxonomy.

A key contract decision for the MVP is capability-first discovery:
- clients should first call `get_project_structure`
- that tool should return both the readable project structure and the supported symbol types for each language present in the project or filtered result set
- clients can then call `parse_file` and `fetch_symbol` using the language-specific capabilities they discovered

This approach is preferable to forcing artificial cross-language unification. Python and TypeScript expose different constructs, and the server should represent those differences honestly while still using a common parser framework and deterministic response envelopes.

# Recommended approach
## Architecture
Adopt a small `src/` package with one FastMCP composition root, three tool modules, and a shared parser subsystem.

The parser subsystem should provide:
- parser registration
- parser lookup by filename / extension
- parser capability discovery
- parser-specific file parsing
- parser-specific symbol lookup with exact source spans

## Critical files to modify
- `/Users/omergilad/workspace/AI/code-explorer-mcp/pyproject.toml`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/main.py`

## Critical files to create
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/server.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/models.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_project_structure.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_file_parse.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/tool_symbol_fetch.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/base.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/common.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/python_parser.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_parser.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/parsing/typescript_bridge.js`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/paths.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/src/code_explorer_mcp/utils/tree.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_project_structure.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_python.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_file_parse_typescript.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_symbol_fetch.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/test_mcp_stdio_integration.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/python_sample.py`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/typescript_sample.ts`
- `/Users/omergilad/workspace/AI/code-explorer-mcp/tests/fixtures/tree_fixture/...`

## Reusable core logic
- `src/code_explorer_mcp/utils/paths.py`: normalize project-relative paths, validate `subfolder` and `filename`, and prevent traversal outside project root.
- `src/code_explorer_mcp/parsing/base.py`: define the shared parser interface and parser registry integration.
- `src/code_explorer_mcp/parsing/common.py`: define shared span models, symbol match models, parser capability models, and deterministic envelope helpers.
- `src/code_explorer_mcp/utils/tree.py`: build a deterministic nested tree from sorted relative paths and render a readable structure string without repeated full-path prefixes.

# Parser abstraction
## Goals
The parser abstraction should provide a uniform way to:
- determine whether a parser supports a file
- report the parser’s language name
- report the parser’s supported symbol types
- parse a file into a deterministic language-specific contract
- fetch an exact symbol snippet from original source text

It should not require all languages to emit identical sections.

## Recommended interface
- `supports(filename: str) -> bool`
- `language() -> str`
- `available_symbol_types() -> list[str]`
- `parse_file(filename: str, source: str) -> ParsedFile`
- `fetch_symbol(filename: str, source: str, symbol: str) -> SymbolMatch | None`

## Abstraction rules
- `tool_file_parse.py` and `tool_symbol_fetch.py` should resolve the parser by file extension and depend only on the shared parser interface.
- Each parser should return a shared envelope plus language-specific symbol sections.
- `available_symbol_types()` defines which top-level sections the parser may emit in `parse_file`.
- The `content` filter passed to `parse_file` must be interpreted against that parser’s `available_symbol_types()` list.
- Each parser must record exact source spans for declarations it can return via `fetch_symbol`.
- Adding a future language should mean registering another parser implementation rather than changing the three-tool API.

# Tool contracts
## 1. `get_project_structure`
### Inputs
- `subfolder: str | None = None`
- `pattern: str | None = None`

### Behavior
- Walk from project root or the requested subfolder.
- Support comma-separated wildcard patterns such as `*.py,*.ts,src/*` using normalized relative paths.
- Return folders and files relative to project root.
- Produce stable output:
  - directories before files
  - alphabetical ordering
  - normalized `/` separators
- Render a readable tree-like structure string where children are shown under parents without repeating the full path on every line.
- Detect which supported languages are present in the matched result set.
- Return available symbol types for each detected language by consulting the registered parsers.

### Output shape
- `root`
- `subfolder`
- `pattern`
- `structure: str`
- `languages_present: list[str]`
- `available_symbol_types_by_language: dict[str, list[str]]`

### Example output
```json
{
  "root": ".",
  "subfolder": null,
  "pattern": "*.py,*.ts",
  "structure": "src/\n  code_explorer_mcp/\n    server.py\n    parsing/\n      python_parser.py\n      typescript_parser.py\ntests/\n  fixtures/\n    python_sample.py\n    typescript_sample.ts",
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
      "re_exports"
    ]
  }
}
```

## 2. `parse_file`
### Inputs
- `filename: str`
- `content: dict | None`

### Behavior
- Resolve the parser from the file extension.
- Parse the file using the selected parser.
- If `content` is omitted, return all symbol sections supported by that parser.
- If `content` is provided, treat its keys as requested symbol types for that file’s language.
- Ignore symbol types that are false.
- Reject unknown symbol types for the selected language with a stable error if FastMCP error handling is deterministic enough for testing.

### Shared output envelope
- `filename`
- `language`
- `available_symbol_types`
- zero or more language-specific symbol sections

### Python contract
#### Python-exposed symbol types
- `imports`
- `globals`
- `classes`
- `functions`

#### Python example output
```json
{
  "filename": "tests/fixtures/python_sample.py",
  "language": "python",
  "available_symbol_types": ["imports", "globals", "classes", "functions"],
  "imports": [
    {"module": "os", "name": null, "alias": null},
    {"module": "typing", "name": "Any", "alias": null}
  ],
  "globals": [
    {"name": "MY_GLOBAL"}
  ],
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
          "inner_classes": []
        }
      ]
    }
  ],
  "functions": [
    {"name": "top_level_function"}
  ]
}
```

### TypeScript contract
#### TypeScript-exposed symbol types
- `imports`
- `globals`
- `classes`
- `functions`
- `interfaces`
- `type_aliases`
- `enums`
- `re_exports`

#### TypeScript example output
```json
{
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
    "re_exports"
  ],
  "imports": [
    {"module": "./types", "default": "Thing", "named": ["Helper"]}
  ],
  "globals": [
    {"name": "TOP_LEVEL_CONST", "declaration_kind": "const"}
  ],
  "classes": [
    {
      "name": "MyClass",
      "members": [{"name": "value"}],
      "methods": [{"name": "run"}],
      "accessors": [{"name": "label", "kind": "getter"}],
      "inner_classes": [
        {
          "name": "InnerClass",
          "members": [],
          "methods": [],
          "accessors": [],
          "inner_classes": []
        }
      ]
    }
  ],
  "functions": [
    {"name": "namedFunction", "syntax": "function"},
    {"name": "arrowFunction", "syntax": "arrow"}
  ],
  "interfaces": [
    {"name": "MyInterface"}
  ],
  "type_aliases": [
    {"name": "MyType"}
  ],
  "enums": [
    {"name": "MyEnum"}
  ],
  "re_exports": [
    {"module": "./shared", "names": ["SharedThing"]}
  ]
}
```

### Common rules for `parse_file`
- section names must be deterministic and documented per language
- ordering inside every section must be deterministic
- output should be intentionally narrow and not expose raw ASTs
- class-like sections may include nested `members`, `methods`, `accessors`, and first-level `inner_classes`
- parsers may include small language-specific nested fields where needed, but top-level sections must come from `available_symbol_types`

## 3. `fetch_symbol`
### Inputs
- `filename: str`
- `symbol: str`

### Supported symbol forms
Support simple dotted paths that map to parser-known declarations.

Examples:
- `my_function`
- `MyClass`
- `MyClass.my_method`
- `MyClass.InnerClass`
- `MY_GLOBAL`
- `MyInterface`
- `MyType`
- `MyEnum`

### Behavior
- Resolve the parser by file extension.
- Parse or consult parser-produced symbol spans.
- Match the requested symbol according to the parser’s language rules.
- Return the exact original source slice for that symbol only.

### Output shape
- `filename`
- `language`
- `symbol`
- `symbol_type`
- `code`

### Example output
```json
{
  "filename": "tests/fixtures/typescript_sample.ts",
  "language": "typescript",
  "symbol": "MyInterface",
  "symbol_type": "interfaces",
  "code": "export interface MyInterface {\n  id: string;\n}"
}
```

### Symbol type rules
- `symbol_type` should be language-specific and come from the parser’s supported capability set.
- Different languages may use different top-level symbol types.
- Shared names such as `classes` or `functions` may overlap across languages, but the system should not force unrelated constructs into a fake universal taxonomy.

# TypeScript parser recommendation
## Recommended option: `ts-morph` via a local Node bridge
The preferred MVP implementation is a small local Node bridge using `ts-morph`.

Why this is the best fit:
- built on the TypeScript compiler API rather than handwritten scanning
- robust support for imports, classes, interfaces, type aliases, enums, functions, accessors, and nested declarations
- reliable source positions and exact source text retrieval for `fetch_symbol`
- lower implementation risk than maintaining a custom parser for evolving TS syntax

Tradeoffs:
- introduces a Node runtime and package dependency in an otherwise Python-first project
- project setup is slightly heavier than a pure Python solution

## Fallback option: Python `tree-sitter` + `tree-sitter-typescript`
Use this only if keeping the stack Python-first is more important than extraction ergonomics.

Why to consider it:
- keeps orchestration in Python
- uses a real grammar rather than regex or ad hoc scanning
- supports structural traversal and source spans

Tradeoffs:
- lower-level traversal work than `ts-morph`
- more manual normalization work for the expanded TypeScript contract
- higher likelihood of implementation complexity around edge constructs

# Parsing details
## Python parsing details
Use `ast.parse` only. This is accurate, dependency-free, and provides `lineno` and `end_lineno` for deterministic symbol fetching.

### Python extraction rules
- include top-level imports
- include module-level globals from assignments and annotated assignments
- include top-level classes
- include direct class members and methods
- include first-level inner classes inside top-level classes
- include top-level functions
- ignore deeper nested classes and functions beyond the first inner-class level
- record exact source spans for all declarations that may be returned by `fetch_symbol`

## TypeScript parsing details
TypeScript and TSX should share the same parser implementation and capability model for MVP unless a TSX-specific construct forces a divergence later.

The MVP TypeScript parser should expose these symbol types:
- `imports`
- `globals`
- `classes`
- `functions`
- `interfaces`
- `type_aliases`
- `enums`
- `re_exports`

### TypeScript extraction rules
At minimum, support deterministic extraction for:
- imports: default, named, and namespace imports
- top-level `const`, `let`, and `var`
- top-level `function` and `async function`
- exported named arrow-function bindings such as `const fn = (...) => {}`
- `class`, `export class`, and `abstract class`
- direct class fields and methods
- getters and setters as accessors within classes
- first-level inner classes inside classes
- `interface` declarations
- `type` aliases
- `enum` declarations
- re-exports: `export { ... } from` and `export * from`
- exact source spans for all declarations returned through parsing or symbol fetch

### Remaining TypeScript limitations to document
Even with the expanded TypeScript symbol set, the MVP may still intentionally simplify or exclude some constructs. These limitations must be documented clearly and covered by tests where relevant:
- decorators and framework-specific metadata details
- computed property names
- complex `namespace` / `module` patterns
- overloaded signature modeling beyond exact declaration capture
- broad object-literal API analysis beyond explicitly supported symbol forms

# Implementation steps
1. Update `pyproject.toml` for a `src/` package layout and add the minimum dependencies:
   - runtime: `fastmcp`
   - TypeScript parsing: Node-side `ts-morph` bridge for the recommended path, or Python `tree-sitter` dependencies for the fallback path
   - test: `pytest`, `pytest-asyncio`
2. Replace `main.py` with a thin entrypoint that imports the FastMCP app and runs it over stdio.
3. Define stable response models in `models.py` before implementing tools so tests can target exact JSON contracts.
4. Implement path normalization and project-root validation in `utils/paths.py`.
5. Implement the shared parser abstraction in `parsing/base.py` and registry / parser-selection wiring in the tool layer.
6. Implement `get_project_structure`:
   - enumerate files under root or subfolder
   - filter by comma-separated wildcard patterns
   - build a deterministic nested tree via `utils/tree.py`
   - render the tree into a readable non-redundant structure string
   - detect which supported languages are present in the result set
   - aggregate `available_symbol_types_by_language` from the registered parsers for those languages
7. Implement Python parsing in `parsing/python_parser.py`:
   - expose Python symbol types: `imports`, `globals`, `classes`, `functions`
   - record source spans for globals, classes, inner classes, methods, and functions
8. Implement TypeScript parsing in `parsing/typescript_parser.py`:
   - preferred: call a small local Node bridge using `ts-morph`
   - fallback: use Python `tree-sitter` bindings with `tree-sitter-typescript`
   - expose TypeScript symbol types: `imports`, `globals`, `classes`, `functions`, `interfaces`, `type_aliases`, `enums`, `re_exports`
   - include inner classes, accessors, and arrow-function bindings in the parser output where appropriate
   - record exact source spans for all symbol types needed by `fetch_symbol`
9. Implement `parse_file` as a wrapper that routes by extension and applies language-aware `content` filtering based on the selected parser’s `available_symbol_types()`.
10. Implement `fetch_symbol` on top of parser-produced symbol spans so the server slices exact original source text and returns the parser-defined `symbol_type`.
11. Build `server.py` as the composition root:
   - instantiate `FastMCP("code-explorer-mcp")`
   - register the three tools
   - keep descriptions and schemas centralized there
12. Add fixture-driven tests for each tool with exact-output assertions.
13. Add a real stdio MCP integration test that launches the local server through the FastMCP client, asserts the tool list, and calls each tool with fixture inputs.

# Verification
## Unit tests
### `tests/test_project_structure.py`
Use a fixed fixture tree and assert exact output for:
- full project structure string
- subfolder structure string
- `*.py`
- `*.py,*.ts`
- folder wildcard cases
- detected `languages_present`
- exact `available_symbol_types_by_language`

### `tests/test_file_parse_python.py`
Use `python_sample.py` with imports, globals, one class, first-level inner class, members, methods, and top-level functions. Assert exact JSON, exact `available_symbol_types`, and exact `content` filtering behavior.

### `tests/test_file_parse_typescript.py`
Use `typescript_sample.ts` with the supported TypeScript symbol types. Assert exact JSON, exact `available_symbol_types`, and exact `content` filtering behavior for:
- `interfaces`
- `type_aliases`
- `enums`
- `functions`
- `classes`
- `re_exports`

### `tests/test_symbol_fetch.py`
Assert exact snippet equality for:
- a Python global
- a Python top-level function
- a Python class
- a Python class method
- a Python inner class
- a TypeScript interface
- a TypeScript type alias
- a TypeScript enum
- a TypeScript arrow-function binding
- a TypeScript class member or accessor

## MCP integration
### `tests/test_mcp_stdio_integration.py`
Use the FastMCP Python client over stdio against the real local server entrypoint.

Verification flow:
1. Start the server as a subprocess client target using the local Python entrypoint.
2. `await client.list_tools()` and assert exact tool names:
   - `get_project_structure`
   - `parse_file`
   - `fetch_symbol`
3. Call each tool with fixture inputs and assert exact JSON output.
4. Verify that `get_project_structure` exposes capability discovery through `languages_present` and `available_symbol_types_by_language`.
5. Add negative tests for unsupported file types, unsupported symbol-type filters, and missing symbols if FastMCP error responses are stable enough to assert exactly.

## Commands to run during verification
- targeted unit tests only:
  - `uv run pytest tests/test_project_structure.py tests/test_file_parse_python.py tests/test_file_parse_typescript.py tests/test_symbol_fetch.py tests/test_mcp_stdio_integration.py`
- optionally run individual tests while iterating on a single tool

## End-to-end checks
- start the server locally over stdio via the Python entrypoint
- confirm the FastMCP client can initialize, list tools, and invoke them successfully
- confirm all outputs use normalized relative paths and deterministic ordering
- confirm `get_project_structure` renders the readable non-redundant structure string exactly as expected
- confirm clients can learn available symbol types from `get_project_structure` and then successfully request language-specific parse sections

# Notes
- Keep responses intentionally narrow and exact; avoid returning raw ASTs.
- Keep all ordering explicit to preserve deterministic tests.
- Do not add broader language support or non-stdio transports in MVP.
- Keep the parser abstraction stable, but allow each language parser to publish its own supported symbol types and output sections.
- `get_project_structure` is the capability-discovery entrypoint: clients should use it to learn both the file layout and the supported symbol types per language before calling parsing tools.