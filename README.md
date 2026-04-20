# code-explorer-mcp

A local FastMCP server that provides deterministic code-exploration primitives for Python and TypeScript repositories.

## Parsing behavior notes

- Python and TypeScript class parsing intentionally expose nested classes only one level deep. A top-level class may include direct `inner_classes`, but classes nested deeper than that are ignored.

## Install

### Install with uv

- `uv tool install code-explorer-mcp`

### Install with pipx

- `pipx install code-explorer-mcp`

### TypeScript parser setup

Python parsing works after install, but TypeScript parsing requires Node.js and npm plus one extra bootstrap step:

1. Install Node.js and npm.
2. Run:
   - `node-setup`

`node-setup` checks that `node` and `npm` are available, then runs `npm install` inside the installed `code_explorer_mcp.parsing` package data.

## Install from source

For local development or GitHub installs:

1. Sync Python dependencies:
   - `uv sync`
2. Install the Node dependencies required by the TypeScript parser runtime:
   - `uv run node-setup`

## Run the server

- Installed package: `code-explorer-mcp`
- Local checkout: `uv run code-explorer-mcp`
