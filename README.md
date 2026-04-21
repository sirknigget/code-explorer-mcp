# code-explorer-mcp

A local FastMCP server that provides deterministic code-exploration primitives for Python and TypeScript repositories.

## Parsing behavior notes

- Python and TypeScript class parsing intentionally expose nested classes only one level deep. A top-level class may include direct `inner_classes`, but classes nested deeper than that are ignored.

## Client setup

This server inspects the current working directory, so your MCP client must launch it from the repository you want to explore.

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

- Installed package: `code-explorer-mcp`
- Local checkout: `uv run code-explorer-mcp`

## Example MCP client config

Claude Code:

```bash
claude mcp add --transport stdio code-explorer -- code-explorer-mcp
```

Generic stdio configuration:

```json
{
  "mcpServers": {
    "code-explorer": {
      "command": "code-explorer-mcp"
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
