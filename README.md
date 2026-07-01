<p align="center">
  <img src="assets/logo.svg" alt="DebugForge Logo" width="200" height="200">
</p>

<h1 align="center">DebugForge</h1>

<p align="center">
  <strong>Bridge Lauterbach TRACE32 to AI Agents via MCP</strong>
</p>

<p align="center">
  <a href="https://github.com/YangPan2020/debugforge/actions"><img src="https://github.com/YangPan2020/debugforge/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-Compatible-purple.svg" alt="MCP"></a>
</p>

<p align="center">
  DebugForge is an MCP server that connects Lauterbach TRACE32 debuggers to AI agents.<br>
  It gives <strong>Claude Code</strong>, <strong>Codex</strong>, <strong>Qwen</strong> and other AI agents direct access to your hardware debugger<br>
  — enabling them to autonomously read target state, locate software bugs, and drive the fix-debug cycle end-to-end.
</p>

---

## Highlights

- **47 MCP Tools** — Full TRACE32 access for AI agents: execution control, breakpoints, memory, registers, variables, symbols, and more
- **Autonomous Debugging** — AI agents can independently connect to your target, reproduce issues, locate root causes, and suggest fixes
- **Project-Aware** — Configure once via `debugforge.toml`, your AI agent automatically knows your ELF paths, flash scripts, and TRACE32 setup
- **Real Hardware** — Battle-tested on TC397 TriCore via USB. Your AI agent controls actual silicon, not a simulator
- **Advanced Breakpoints** — Conditional, data watchpoints, hit-count, task-specific, action triggers, and temporary breakpoints
- **Deep Inspection** — AI agents can read call stacks with locals, expand structs, view disassembly, inspect peripherals
- **Any MCP Agent** — Works with Claude Code, Codex CLI, Qwen, or any MCP-compatible AI assistant
- **Zero Lock-in** — MIT licensed, open source, no vendor dependencies beyond TRACE32 itself

## Architecture

```
┌─────────────────┐         MCP (stdio)         ┌──────────────┐       PYRCL/TCP       ┌──────────────┐
│                 │◄───────────────────────────►│              │◄─────────────────────►│              │
│   AI Agent      │   JSON-RPC tool calls        │  DebugForge  │   Remote Control API  │   TRACE32    │
│  (Claude Code,  │   (47 debugging tools)       │  MCP Server  │   (lauterbach-trace32 │  PowerView   │
│   Codex, etc.)  │                              │              │    -rcl)              │              │
│                 │◄───────────────────────────►│              │◄─────────────────────►│              │
└─────────────────┘         Results              └──────────────┘       Hardware         └──────┬───────┘
                                                                                               │
                                                                                        ┌──────▼───────┐
                                                                                        │   Target MCU  │
                                                                                        │  (e.g. TC397) │
                                                                                        └──────────────┘
```

## Quick Start

```bash
# 1. Install DebugForge
pip install debugforge

# 2. Install TRACE32 Python package (from your TRACE32 installation)
pip install <YOUR_T32_PATH>/demo/api/python/rcl/dist/lauterbach_trace32_rcl-*.whl

# 3. Add to your AI agent's MCP config (e.g. .claude/settings.json)
```

```json
{
  "mcpServers": {
    "debugforge": {
      "command": "debugforge"
    }
  }
}
```

```bash
# 4. Start TRACE32 with API port enabled, then ask your AI agent:
#    "Connect to TRACE32, load the firmware, find why the system crashes at boot"
```

## Installation

### Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.10 or higher |
| TRACE32 | PowerView running with Remote API enabled |
| PYRCL | `lauterbach-trace32-rcl` package from your TRACE32 installation |

### Step 1: Install DebugForge

```bash
pip install debugforge
```

Or install from source:

```bash
git clone https://github.com/YangPan2020/debugforge.git
cd debugforge
pip install -e .
```

### Step 2: Install TRACE32 Python Library

The PYRCL wheel is bundled with your TRACE32 installation:

```bash
pip install <T32_INSTALL_PATH>/demo/api/python/rcl/dist/lauterbach_trace32_rcl-*.whl
```

> Replace `<T32_INSTALL_PATH>` with your TRACE32 installation directory (e.g., `/opt/t32`, `C:\T32`).

### Step 3: Enable TRACE32 Remote API

Add these lines to your TRACE32 configuration file (`.t32` or `config.t32`):

```
RCL=NETTCP
PORT=20000
```

Then restart TRACE32 PowerView.

## Configuration

### MCP Client Setup

<details>
<summary><strong>Claude Code</strong></summary>

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "debugforge": {
      "command": "debugforge"
    }
  }
}
```

</details>

<details>
<summary><strong>Claude Code (with auto-connect)</strong></summary>

```json
{
  "mcpServers": {
    "debugforge": {
      "command": "debugforge",
      "env": {
        "T32_AUTO_CONNECT": "true",
        "T32_PORT": "20000"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Other MCP Clients</strong></summary>

Any MCP-compatible client can use DebugForge. Configure the command as `debugforge` with stdio transport.

</details>

### Project Configuration (`debugforge.toml`)

Create a `debugforge.toml` in your project root to tell your AI agent about your debugging environment:

```toml
[trace32]
install_path = "/opt/t32"                      # TRACE32 installation directory

[connection]
node = "localhost"                              # TRACE32 host address
port = 20000                                   # API port (match your .t32 config)
protocol = "TCP"                               # TCP or UDP
auto_connect = true                            # Connect when server starts

[project]
elf = "output/build/firmware.elf"              # ELF file with debug symbols
map = "output/build/firmware.map"              # MAP file (optional)

[scripts]
flash = "tools/Trace32/flash.cmm"             # Flash programming script
init = "tools/Trace32/startup.cmm"            # Target init script
```

All relative paths are resolved from the directory containing `debugforge.toml`.

See [`debugforge.example.toml`](debugforge.example.toml) for a complete template.

### Environment Variables

Environment variables override `debugforge.toml` values (highest priority):

| Variable | Default | Description |
|----------|---------|-------------|
| `T32_INSTALL_PATH` | — | TRACE32 installation directory |
| `T32_NODE` | `localhost` | TRACE32 host address |
| `T32_PORT` | `20000` | TRACE32 API port |
| `T32_PROTOCOL` | `TCP` | Communication protocol (TCP/UDP) |
| `T32_AUTO_CONNECT` | `false` | Auto-connect on server start |
| `DEBUGFORGE_CONFIG` | `./debugforge.toml` | Path to config file |

**Priority:** Environment Variables > `debugforge.toml` > Built-in Defaults

## Available Tools (47)

### Connection & Configuration

| Tool | Description |
|------|-------------|
| `connect` | Connect to a TRACE32 PowerView instance |
| `disconnect` | Disconnect from TRACE32 |
| `status` | Get connection status, TRACE32 version, and system state |
| `get_project_config` | Get the loaded project configuration (paths, scripts, settings) |

### Execution Control

| Tool | Description |
|------|-------------|
| `go` | Start/continue program execution |
| `step` | Single-step execution (into, over, or out) |
| `halt` | Stop program execution |
| `reset` | Reset the target CPU |
| `get_state` | Get current CPU execution state |
| `go_till` | Run until a specific address (temporary breakpoint) |
| `go_up` | Run until current function returns to caller |
| `go_return` | Run to the return instruction of current function |

### Breakpoints

| Tool | Description |
|------|-------------|
| `set_breakpoint` | Set a program/read/write/readwrite breakpoint |
| `list_breakpoints` | List all active breakpoints |
| `delete_breakpoint` | Delete a breakpoint |
| `toggle_breakpoint` | Enable/disable a breakpoint without deleting |

### Advanced Breakpoints

| Tool | Description |
|------|-------------|
| `set_conditional_breakpoint` | Breakpoint with HLL condition (e.g., `i > 100`) |
| `set_data_breakpoint` | Trigger on memory access with optional value match |
| `set_count_breakpoint` | Stop after N-th hit (loop debugging) |
| `set_task_breakpoint` | Trigger only for a specific OS task/thread |
| `set_action_breakpoint` | Execute a TRACE32 command on hit |
| `set_temporary_breakpoint` | Auto-deletes after first hit |

### Memory

| Tool | Description |
|------|-------------|
| `read_memory` | Read target memory (hex dump format) |
| `write_memory` | Write data to target memory |
| `data_set` | Write a value to a memory address using Data.Set |

### Registers

| Tool | Description |
|------|-------------|
| `read_register` | Read a single CPU register |
| `read_registers` | Read multiple registers at once |
| `write_register` | Write a value to a CPU register |

### Variables

| Tool | Description |
|------|-------------|
| `read_variable` | Read a C/C++ variable by symbol name |
| `write_variable` | Write a value to a C/C++ variable |
| `var_view` | View a variable/struct/array with full expansion |
| `var_set` | Set a C/C++ variable to a new value |

### Symbols

| Tool | Description |
|------|-------------|
| `symbol_by_name` | Look up symbol address by name |
| `symbol_by_address` | Look up symbol name by address |

### Commands & Scripting

| Tool | Description |
|------|-------------|
| `execute_command` | Execute any TRACE32 PRACTICE command |
| `run_practice` | Run a PRACTICE (.cmm) script with timeout |
| `evaluate` | Evaluate a TRACE32 expression or function |

### Debug Views

| Tool | Description |
|------|-------------|
| `get_callstack` | Get call stack with function names |
| `get_locals` | Get call stack with all local variables per frame |
| `get_data_dump` | Formatted memory dump (hex + ASCII) |
| `get_register_view` | Full register view with all flags |
| `get_disassembly` | Disassembly listing at address or current PC |
| `get_source_listing` | Source code around current execution point |
| `get_window` | Get text content of any TRACE32 window command |

### System & OS Awareness

| Tool | Description |
|------|-------------|
| `get_task_list` | List OS tasks/threads |
| `get_task_stack` | Get stack info for OS tasks |
| `get_peripheral_view` | View peripheral register contents |

## Usage Examples

### Basic Debug Session

```
You: "Connect to TRACE32 and help me find why the system crashes after boot"

AI Agent workflow:
  1. get_project_config()           → learns your ELF path and scripts
  2. connect()                      → connects to TRACE32
  3. execute_command("SYStem.Up")   → powers up the target
  4. execute_command("Data.LOAD.Elf /path/to/firmware.elf")
  5. set_breakpoint("main")
  6. go()                           → runs to main
  7. step("over")                   → steps through code
  8. get_callstack()                → analyzes the call stack
  9. read_variable("error_code")    → checks variables
  → "Found it: error_code = -1 because init_hardware() fails at line 84"
```

### Flash and Debug

```
You: "Flash the new firmware and verify it boots correctly"

AI Agent workflow:
  1. get_project_config()           → gets flash script path
  2. connect()
  3. run_practice("tools/flash.cmm")  → flashes firmware
  4. reset()
  5. set_breakpoint("main")
  6. go()
  7. get_state()                    → confirms target stopped at main
  → "Firmware flashed and verified — target stopped at main() successfully"
```

### Advanced Debugging

```
You: "The buffer overflow happens somewhere in process_packet(). Set a watchpoint."

AI Agent workflow:
  1. symbol_by_name("rx_buffer")    → gets buffer address
  2. set_data_breakpoint(address="0xD0001000", access="write", size=256)
  3. go()
  4. get_callstack()                → sees who wrote beyond the buffer
  5. get_disassembly()              → examines the offending instruction
  6. read_memory("0xD0001000", 512) → shows the corrupted data
  → "Overflow at process_packet+0x4C: memcpy writes 320 bytes into 256-byte buffer"
```

## Supported AI Agents

| Agent | Status | Configuration |
|-------|--------|---------------|
| [Claude Code](https://claude.com/claude-code) | ✅ Tested | `.claude/settings.json` |
| [Codex CLI](https://github.com/openai/codex) | ✅ Compatible | MCP stdio transport |
| [Qwen Agent](https://github.com/QwenLM/Qwen-Agent) | ✅ Compatible | MCP stdio transport |
| Any MCP Client | ✅ Compatible | Standard MCP protocol |

## Development

### Setup

```bash
git clone https://github.com/YangPan2020/debugforge.git
cd debugforge
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

- [ ] HTTP/SSE transport for remote debugging
- [ ] Auto-start/manage TRACE32 lifecycle
- [ ] ELF/MAP static analysis tools
- [ ] Multi-core debugging (multiple simultaneous connections)
- [ ] Trace data analysis and visualization
- [ ] Flash programming tools (dedicated, beyond script execution)

## License

[MIT](LICENSE) — free for personal and commercial use.

---

<p align="center">
  <sub>Built with ❤️ for the embedded debugging community</sub>
</p>
