# mcp-trace32 Design Specification

**Date:** 2026-06-30
**Status:** Approved
**Author:** lixiang

## Overview

mcp-trace32 is an open-source MCP (Model Context Protocol) server that bridges Lauterbach TRACE32 debuggers to AI agents (Claude Code, Codex, Qwen, etc.). It wraps the official `lauterbach.trace32.rcl` (PYRCL) Python package as MCP tools, enabling AI agents to perform hardware debugging operations — read/write memory, set breakpoints, step through code, inspect variables — through a standardized protocol.

## Goals

1. Enable AI agents to directly control TRACE32 debuggers via MCP
2. Provide granular, 1:1 mapped tools for all core debugging operations
3. Keep the server focused — users bring their own running TRACE32 instance
4. MIT licensed for maximum adoption in the embedded industry

## Non-Goals (v1.0)

- Auto-starting/managing TRACE32 lifecycle
- ELF/MAP file parsing (future enhancement)
- HTTP/SSE transport (future enhancement)
- Multi-connection management (one debugger at a time)

## Target Audience

Embedded developers already familiar with TRACE32 and PRACTICE scripting, who want AI to help automate repetitive debug workflows.

## Architecture

```
┌─────────────────────┐     stdio      ┌──────────────────┐     TCP/UDP     ┌──────────────┐
│  AI Agent           │◄──────────────►│  mcp-trace32     │◄──────────────►│  TRACE32     │
│  (Claude Code,      │   JSON-RPC     │  (MCP Server)    │   PYRCL/RCL    │  PowerView   │
│   Codex, etc.)      │                │                  │                │  (Debugger)  │
└─────────────────────┘                └──────────────────┘                └──────────────┘
```

### Transport

- **stdio only** — Server runs as subprocess of the AI agent
- Communication via JSON-RPC 2.0 over stdin/stdout

### Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]` | MCP Python SDK with FastMCP |
| `lauterbach-trace32-rcl` | Official PYRCL package for TRACE32 Remote API |

### Python Version

Python 3.10+

## Project Structure

```
mcp-trace32/
├── src/mcp_trace32/
│   ├── __init__.py            # Package version + public API
│   ├── __main__.py            # Entry point: python -m mcp_trace32
│   ├── server.py              # FastMCP instance, lifespan, tool registration
│   ├── state.py               # Global connection state (Debugger reference)
│   └── tools/
│       ├── __init__.py        # Tool registration helper
│       ├── connection.py      # connect, disconnect, status
│       ├── execution.py       # go, step, halt, reset, get_state
│       ├── memory.py          # read_memory, write_memory
│       ├── registers.py       # read_register, read_registers, write_register
│       ├── breakpoints.py     # set_breakpoint, list_breakpoints, delete_breakpoint, toggle_breakpoint
│       ├── variables.py       # read_variable, write_variable
│       ├── symbols.py         # symbol_by_name, symbol_by_address
│       └── commands.py        # execute_command, run_practice, evaluate
├── tests/
│   ├── conftest.py
│   ├── test_connection.py
│   ├── test_execution.py
│   ├── test_memory.py
│   └── ...
├── pyproject.toml
├── README.md
├── LICENSE                    # MIT
└── .github/
    └── workflows/
        └── ci.yml
```

## Tool Definitions

### Connection (3 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `connect` | `node: str = "localhost"`, `port: int = 20000`, `protocol: str = "TCP"` | Success message with TRACE32 software version |
| `disconnect` | — | Confirmation message |
| `status` | — | Connection state, T32 version, target CPU state |

### Execution Control (5 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `go` | — | Confirmation that execution started |
| `step` | `mode: str = "into"` (into/over/out) | New PC address after step |
| `halt` | — | CPU state after halt |
| `reset` | — | Confirmation of target reset |
| `get_state` | — | Current CPU state (running/stopped/power-down/error) |

### Memory (2 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `read_memory` | `address: str`, `length: int`, `width: int = 32`, `access: str = ""` | Hex dump of memory contents |
| `write_memory` | `address: str`, `data: str` (hex), `width: int = 32`, `access: str = ""` | Confirmation with bytes written |

### Registers (3 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `read_register` | `name: str` | Register name and value |
| `read_registers` | `names: list[str] = []`, `core: str = ""` | List of register name/value pairs |
| `write_register` | `name: str`, `value: int` | Confirmation with new value |

### Variables (2 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `read_variable` | `name: str` | Variable name, value, and type |
| `write_variable` | `name: str`, `value: str` | Confirmation with new value |

### Symbols (2 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `symbol_by_name` | `name: str` | Symbol address and size |
| `symbol_by_address` | `address: str` | Symbol name |

### Breakpoints (4 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `set_breakpoint` | `address: str`, `type: str = "program"` (program/read/write/readwrite), `impl: str = "auto"` (auto/soft/hard) | Breakpoint details |
| `list_breakpoints` | — | All active breakpoints with details |
| `delete_breakpoint` | `address: str` | Confirmation |
| `toggle_breakpoint` | `address: str`, `enabled: bool` | New state |

### Commands & Scripting (3 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `execute_command` | `command: str` | Success/error with any message output |
| `run_practice` | `script: str`, `timeout: float = 60.0` | Script result (message or eval value) |
| `evaluate` | `expression: str` | PRACTICE function evaluation result |

**Total: 24 tools**

## Connection State Management

```python
class T32State:
    debugger: Debugger | None = None
    node: str = ""
    port: int = 0
    protocol: str = ""
    connected: bool = False
```

- Single global state instance shared across all tools
- Managed via FastMCP lifespan context for cleanup on exit
- All tools check `state.connected` before operating; return clear error if not connected

## Error Handling

### Principles

1. All tools validate connection state first
2. PYRCL exceptions are caught and converted to structured error messages
3. No tool crashes the MCP server process
4. Errors include actionable guidance for the AI agent

### Error Categories

| Category | Example | Response |
|----------|---------|----------|
| Not connected | Any tool called before `connect` | `"Not connected to TRACE32. Call 'connect' tool first."` |
| Connection failed | Wrong port, T32 not running | `"Failed to connect to TRACE32 at localhost:20000 - Connection refused"` |
| Command error | Invalid TRACE32 command | `"TRACE32 command error: <message from T32 message line>"` |
| Target state error | Read memory while CPU running | `"Cannot read memory: target is running. Call 'halt' first."` |

## Configuration

### Claude Code Integration

```json
{
  "mcpServers": {
    "trace32": {
      "command": "uvx",
      "args": ["mcp-trace32"]
    }
  }
}
```

### Environment Variables (optional auto-connect)

| Variable | Default | Purpose |
|----------|---------|---------|
| `T32_NODE` | `localhost` | TRACE32 host |
| `T32_PORT` | `20000` | TRACE32 API port |
| `T32_PROTOCOL` | `TCP` | Protocol (TCP/UDP) |
| `T32_AUTO_CONNECT` | `false` | Auto-connect on server start |

## Packaging & Distribution

- **PyPI package name:** `mcp-trace32`
- **Import name:** `mcp_trace32`
- **Entry point:** `mcp-trace32` CLI command (via pyproject.toml scripts)
- **Build system:** hatchling
- **PYRCL dependency:** Users must install `lauterbach-trace32-rcl` separately from their TRACE32 installation (cannot be distributed on PyPI due to Lauterbach licensing)

## Testing Strategy

- Unit tests mock the PYRCL `Debugger` object
- Integration tests require a running TRACE32 Instruction Set Simulator (ISS)
- CI runs unit tests only; integration tests are manual or require T32 ISS license

## Future Enhancements (post v1.0)

1. HTTP/SSE transport for remote access
2. Auto-start TRACE32 lifecycle management
3. ELF/MAP parsing tools for static analysis
4. Multi-core debugging support (multiple simultaneous connections)
5. Trace analyzer data access
6. Flash programming tools
