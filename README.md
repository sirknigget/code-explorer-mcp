# code-explorer-mcp

This repository currently includes a proof of concept TypeScript parser under `src/ts_parser_poc`.

## Setup

1. Sync Python dependencies:
   - `uv sync`
2. Install the Node dependencies required by the ts-morph POC:
   - `uv run ts-parser-poc-setup`

The setup command checks that `node` and `npm` are installed before running `npm install` inside `src/ts_parser_poc`.

## Run the POC

- `uv run ts-parser-poc`

The runner assumes the setup step has already been completed. If `node_modules` is missing, it will stop and tell you to run `uv run ts-parser-poc-setup` first.
