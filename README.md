# code-explorer-mcp

A local FastMCP server that provides deterministic code-exploration primitives for Python and TypeScript repositories.

## Setup

1. Sync Python dependencies:
   - `uv sync`
2. Install the Node dependencies required by the TypeScript parser runtime:
   - `uv run node-setup`

The setup command checks that `node` and `npm` are installed before running `npm install` inside `src/code_explorer_mcp/parsing`.

## Run the server

- `uv run code-explorer-mcp`
