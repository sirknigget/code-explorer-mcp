# code-explorer-mcp

A local FastMCP server that provides deterministic code-exploration primitives for Python and TypeScript repositories.

It is designed for agentic workflows that need fast, structured answers about a codebase without repeatedly scanning raw files. Instead of returning full ASTs or loose text summaries, it exposes a small set of tools that answer three common questions reliably:

- What does this repo or subtree look like?
- What symbols are available in this file?
- What is the exact source for this symbol?

## What it's good for

`code-explorer-mcp` works best as a low-noise index and retrieval layer for coding agents, MCP clients, and automation that need deterministic code navigation.

Typical use cases:

- Quickly map a repository or a filtered subtree before deeper inspection.
- Discover language capabilities available in the current project, including which symbol sections a parser supports.
- Parse a file into stable symbol lists such as functions, classes, imports, interfaces, or enums.
- Fetch the exact source of a known symbol after discovering it through `parse_file`.
- Reduce token usage in agent loops by avoiding repeated full-file reads when only symbol discovery or exact symbol extraction is needed.

It is not trying to be a general static analysis platform, cross-reference engine, or full semantic search system. The value is predictable, bounded output that is easy for tools and agents to consume.

## MCP capabilities

The server exposes three tools:

### `get_project_structure`

Returns a deterministic tree view of the selected project root or subfolder and reports which parser capabilities are available for the matched files.

Useful for:

- getting the high-level layout of a repo
- scoping exploration to a subtree such as `src`
- filtering by glob patterns such as `*.py` or `*.ts,*.tsx`
- discovering which languages and symbol sections are available before calling `parse_file`

Behavior notes:

- respects `.gitignore`
- skips a built-in set of common ignored directories
- trims the rendered tree to the requested subtree in the MCP response
- returns language-to-symbol-type capability data alongside the tree

### `parse_file`

Parses a supported file and returns a deterministic, language-specific envelope summarized into MCP-friendly sections.

Useful for:

- listing top-level functions, classes, globals, and imports
- inspecting TypeScript-specific sections such as interfaces, type aliases, enums, and re-exports
- requesting only the sections you need with the `content` selector map

Behavior notes:

- paths are project-relative and validated against the configured project root
- unsupported file types or unknown requested sections return structured errors
- MCP output is intentionally compact: sections are presented as lists of names or rendered import/export statements rather than raw parser objects

### `fetch_symbol`

Returns the exact source code for a parser-known symbol in a supported file.

Useful for:

- extracting a single function, class, interface, enum, or other parser-known symbol without reading the whole file
- following a `parse_file` call with exact source retrieval for the symbol you want to inspect or modify

Behavior notes:

- expects the exact symbol name returned by `parse_file`
- returns structured errors for invalid paths, unsupported requests, unreadable files, and missing symbols
- includes `symbol_type` when the parser can identify it

## Supported languages and symbol sections

Current language support:

- Python
- TypeScript

Available sections depend on the parser:

- Python: `imports`, `globals`, `classes`, `functions`
- TypeScript: `imports`, `globals`, `classes`, `functions`, `interfaces`, `type_aliases`, `enums`, `re_exports`

## Parsing behavior notes

- Python and TypeScript class parsing intentionally expose nested classes only one level deep. A top-level class may include direct `inner_classes`, but classes nested deeper than that are ignored.

## Client setup

This server inspects the current working directory by default, or an explicit path when you pass `--path`.

### Recommended install

Install the server as a tool:

- `uv tool install code-explorer-mcp`

This makes `code-explorer-mcp` and `code-explorer-node-setup` available as global commands if your uv tool bin directory is on `PATH`.

If you prefer `pipx`:

- `pipx install code-explorer-mcp`

### TypeScript parser setup

Python parsing works after install. TypeScript parsing also requires Node.js and npm plus one bootstrap step:

1. Install Node.js and npm.
2. Run:
   - `code-explorer-node-setup`

`code-explorer-node-setup` checks that `node` and `npm` are available, then installs the TypeScript parser runtime inside the installed package.

## Run the server

By default, the server inspects the current working directory. Use `--path` when you want to inspect a different repository without changing directories.

- Installed package: `code-explorer-mcp`
- Installed package with explicit target repo: `code-explorer-mcp --path /path/to/repo`
- Local checkout: `uv run code-explorer-mcp`
- Local checkout with explicit target repo: `uv run code-explorer-mcp --path /path/to/repo`

## Example MCP client config

Claude Code:

```bash
claude mcp add --transport stdio code-explorer -- code-explorer-mcp --path /path/to/repo
```

Generic stdio configuration:

```json
{
  "mcpServers": {
    "code-explorer": {
      "command": "code-explorer-mcp",
      "args": ["--path", "/path/to/repo"]
    }
  }
}
```

If you installed with `pipx`, the command stays `code-explorer-mcp` and the setup command is `code-explorer-node-setup`.

## Install from source

For local development or GitHub installs:

1. Sync Python dependencies:
   - `uv sync`
2. Install the Node dependencies required by the TypeScript parser runtime:
   - `uv run code-explorer-node-setup`
3. Run the server from the repository you want to inspect:
   - `uv run code-explorer-mcp`
   - or from anywhere with an explicit target: `uv run code-explorer-mcp --path /path/to/repo`
