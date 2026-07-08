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
  — enabling them to autonomously read target state, locate software bugs, and drive the fix-debug cycle end-to-end.<br>
  Supports both <strong>local</strong> and <strong>remote</strong> (WinRM/SSH) TRACE32 environments.
</p>

---

## Highlights

- **47 MCP Tools** — Full TRACE32 access for AI agents: execution control, breakpoints, memory, registers, variables, symbols, and more
- **Autonomous Debugging** — AI agents can independently connect to your target, reproduce issues, locate root causes, and suggest fixes
- **Local + Remote** — Debug locally or connect to a remote Windows TRACE32 via WinRM/SSH with full file transfer support
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

### Remote Mode

```
┌─────────────────────────────────────────────────────────────┐
│  Local Linux (Agent)                                        │
│  - Source/ELF/CMM files                                     │
│  - AI Agent (DebugForge MCP Server)                         │
└────────────────┬────────────────────────┬───────────────────┘
                 │ SCP/WinRM              │ PYRCL (port 20000)
                 │ File transfer          │ Remote control
                 ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Remote Windows                                             │
│  - TRACE32 PowerView                                        │
│  - Hardware target (TC38x/TC39x)                            │
└─────────────────────────────────────────────────────────────┘
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
# 4. Configure your project
cp debugforge.toml.example debugforge.toml
# Edit debugforge.toml with your paths and connection settings

# 5. Start TRACE32 with API port enabled, then ask your AI agent:
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

### Step 3: Enable TRACE32 Remote API

Add these lines to your TRACE32 configuration file (`.t32` or `config.t32`):

```
RCL=NETTCP
PORT=20000
```

Then restart TRACE32 PowerView.

## Configuration

### Project Configuration (`debugforge.toml`)

Create a `debugforge.toml` in your project root. A complete template is provided:

```bash
cp debugforge.toml.example debugforge.toml
```

```toml
[mode]
mode = "local"  # "local" or "remote"

[connection]
node = "localhost"
port = 20000
protocol = "TCP"
auto_connect = true

[remote]
host = "192.168.1.100"
winrm_port = 5985
winrm_user = "user@domain.local"
winrm_password = "your_password"
ssh_user = "username"
staging_dir = "D:\\T32\\debugforge"

[project]
elf = "output/build/firmware.elf"

[scripts]
flash = "tools/Trace32/flash.cmm"
```

> **Note**: `debugforge.toml` contains credentials and is gitignored. Never commit it.

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
| `get_source_location` | Get current source file and line |
| `get_current_function` | Get name of currently executing function |
| `get_run_stats` | Combined run/halt statistics |

### Breakpoints

| Tool | Description |
|------|-------------|
| `set_breakpoint` | Set a program/read/write/readwrite breakpoint |
| `list_breakpoints` | List all active breakpoints |
| `delete_breakpoint` | Delete a breakpoint |
| `clear_all_breakpoints` | Delete all breakpoints at once |
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
| `read_memory_cached` | Read through CPU data cache |
| `read_memory_physical` | Read bypassing cache |

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
| `get_window` | Get text content of any TRACE32 window command |

### Multicore

| Tool | Description |
|------|-------------|
| `select_core` | Switch debugger focus to a specific core |
| `get_chip_info` | Get chip stepping and configuration |
| `get_all_cores_state` | Get execution state of all cores |
| `sync_cores` | Synchronized Go/Break/Step across cores |

### On-chip Trace (MCDS)

| Tool | Description |
|------|-------------|
| `trace_start` | Configure and start trace recording |
| `trace_stop` | Stop trace recording |
| `trace_list` | Display trace buffer contents |
| `trace_clear` | Clear trace buffer |
| `trace_set_trigger` | Set trace start/stop triggers |

### System Configuration

| Tool | Description |
|------|-------------|
| `set_reset_behavior` | Configure reset handling |
| `set_cache_read` | Enable/disable cache-aware reads |
| `set_peripheral_suspend` | Suspend peripherals on halt |
| `load_symbol_file` | Load ELF debug symbols |
| `get_system_options` | Get all system option settings |

## Usage Examples

### Basic Debug Session

```
You: "Connect to TRACE32 and help me find why the system crashes after boot"

AI Agent workflow:
  1. get_project_config()           → learns your ELF path and scripts
  2. connect()                      → connects to TRACE32
  3. run_practice("flash.cmm")      → flashes firmware
  4. set_breakpoint("main")
  5. go()                           → runs to main
  6. step("over")                   → steps through code
  7. get_callstack()                → analyzes the call stack
  8. read_variable("error_code")    → checks variables
  → "Found it: error_code = -1 because init_hardware() fails at line 84"
```

### Remote Debug Session

```
You: "Connect to the remote TRACE32 on Windows and debug the TC397 board"

AI Agent workflow:
  1. get_project_config()           → detects remote mode, gets WinRM credentials
  2. connect(node="192.168.1.100")  → connects via PYRCL over network
  3. run_practice("tc39x_flash.cmm") → flashes via remote TRACE32
  4. go() → halt() → get_callstack()
  → Debugging the remote target as if it were local
```

## Supported AI Agents

| Agent | Status | Configuration |
|-------|--------|---------------|
| [Claude Code](https://claude.com/claude-code) | ✅ Tested | `.claude/settings.json` |
| [Codex CLI](https://github.com/openai/codex) | ✅ Compatible | MCP stdio transport |
| [Qwen Agent](https://github.com/QwenLM/Qwen-Agent) | ✅ Compatible | MCP stdio transport |
| Any MCP Client | ✅ Compatible | Standard MCP protocol |

## File Structure

```
debugforge/
├── src/debugforge/          # MCP Server core
│   ├── server.py            # FastMCP server entry
│   ├── config.py            # Configuration (local + remote)
│   ├── state.py             # Connection state management
│   └── tools/               # Tool implementations (47 tools)
├── examples/                # Example scripts
│   ├── remote_debug.py      # Remote debug via WinRM + PYRCL
│   ├── remote_debug_tc38x.py
│   ├── test_all_tools.py    # Full tool verification
│   └── debug_tc397_live.py  # TC397 complete workflow
├── debugforge.toml.example  # Configuration template
├── WINDOWS_SSH_SETUP.md     # Remote Windows setup guide
└── README.md
```

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

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## License

[MIT](LICENSE) — free for personal and commercial use.

---

<p align="center">
  <sub>Built with ❤️ for the embedded debugging community</sub>
</p>
