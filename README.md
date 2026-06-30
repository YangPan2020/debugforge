# mcp-trace32

An MCP (Model Context Protocol) server that connects AI agents to Lauterbach TRACE32 debuggers.

Enables Claude Code, Codex, Qwen, and other AI coding agents to perform hardware debugging operations — read/write memory, set breakpoints, step through code, inspect variables — through the standardized MCP protocol.

## Prerequisites

- Python 3.10+
- A running TRACE32 PowerView instance with API port enabled
- `lauterbach-trace32-rcl` package (from your TRACE32 installation)

## Installation

```bash
pip install mcp-trace32
```

For the PYRCL dependency, install from your TRACE32 installation:

```bash
pip install /opt/t32/demo/api/python/rcl/dist/lauterbach_trace32_rcl-*.whl
```

## Configuration

### Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "trace32": {
      "command": "mcp-trace32"
    }
  }
}
```

### TRACE32 Setup

Ensure your TRACE32 config file has the API port enabled:

```
RCL=NETTCP
PORT=20000
```

## Usage

Once configured, the AI agent can use tools like:

- `connect` — Connect to a running TRACE32 instance
- `read_memory` — Read memory at an address
- `read_register` — Read CPU register values
- `set_breakpoint` — Set a breakpoint
- `step` — Single-step execution
- `execute_command` — Run any TRACE32 command

## Available Tools

| Category | Tools |
|----------|-------|
| Connection | `connect`, `disconnect`, `status` |
| Execution | `go`, `step`, `halt`, `reset`, `get_state` |
| Memory | `read_memory`, `write_memory` |
| Registers | `read_register`, `read_registers`, `write_register` |
| Variables | `read_variable`, `write_variable` |
| Symbols | `symbol_by_name`, `symbol_by_address` |
| Breakpoints | `set_breakpoint`, `list_breakpoints`, `delete_breakpoint`, `toggle_breakpoint` |
| Commands | `execute_command`, `run_practice`, `evaluate` |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `T32_NODE` | `localhost` | TRACE32 host |
| `T32_PORT` | `20000` | TRACE32 API port |
| `T32_PROTOCOL` | `TCP` | Protocol (TCP/UDP) |
| `T32_AUTO_CONNECT` | `false` | Auto-connect on server start |

## License

MIT
