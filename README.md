# DebugForge

**AI-Powered Debugging for Lauterbach TRACE32**

DebugForge is an MCP (Model Context Protocol) server that connects AI agents to Lauterbach TRACE32 debuggers. It enables Claude Code, Codex, Qwen, and other AI coding agents to perform hardware debugging operations — set breakpoints, inspect call stacks, read variables, step through code — through the standardized MCP protocol.

> 🔧 Forge your debugging workflow with AI — from code generation to bug resolution, all in one loop.

## Prerequisites

- Python 3.10+
- A running TRACE32 PowerView instance with API port enabled
- `lauterbach-trace32-rcl` package (from your TRACE32 installation)

## Installation

```bash
pip install debugforge
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
    "debugforge": {
      "command": "debugforge"
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

## What Can It Do?

DebugForge gives your AI agent **46 debugging tools** — everything you'd do manually in TRACE32:

### Debug Session Flow

```
AI Agent: "连接调试器并定位这个 crash"

→ connect(port=20000)                    # 连接 TRACE32
→ execute_command("SYStem.Up")           # 连接目标芯片  
→ execute_command("Data.LOAD.Elf ...")   # 加载 ELF
→ set_breakpoint("main")                 # 设断点
→ go()                                   # 运行
→ get_callstack()                        # 查看调用栈
→ get_locals()                           # 查看局部变量
→ read_memory("0xD0000000", 64)          # 读内存
→ step("over")                           # 单步
→ var_view("myStruct")                   # 查看数据结构
→ "Bug found: null pointer at line 42"   # AI 分析结论
```

## Available Tools (46)

| Category | Tools |
|----------|-------|
| **Connection** | `connect`, `disconnect`, `status` |
| **Execution** | `go`, `step`, `halt`, `reset`, `get_state`, `go_till`, `go_up`, `go_return` |
| **Breakpoints** | `set_breakpoint`, `list_breakpoints`, `delete_breakpoint`, `toggle_breakpoint` |
| **Advanced BP** | `set_conditional_breakpoint`, `set_data_breakpoint`, `set_count_breakpoint`, `set_task_breakpoint`, `set_action_breakpoint`, `set_temporary_breakpoint` |
| **Memory** | `read_memory`, `write_memory`, `data_set` |
| **Registers** | `read_register`, `read_registers`, `write_register` |
| **Variables** | `read_variable`, `write_variable`, `var_set`, `var_view` |
| **Symbols** | `symbol_by_name`, `symbol_by_address` |
| **Commands** | `execute_command`, `run_practice`, `evaluate` |
| **Debug Views** | `get_callstack`, `get_locals`, `get_data_dump`, `get_register_view`, `get_disassembly`, `get_source_listing`, `get_window` |
| **System/OS** | `get_task_list`, `get_task_stack`, `get_peripheral_view` |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `T32_NODE` | `localhost` | TRACE32 host |
| `T32_PORT` | `20000` | TRACE32 API port |
| `T32_PROTOCOL` | `TCP` | Protocol (TCP/UDP) |
| `T32_AUTO_CONNECT` | `false` | Auto-connect on server start |

## Why DebugForge?

- **Complete** — 46 tools cover the full TRACE32 debugging workflow
- **Real Hardware** — Tested on actual TC397 TriCore hardware via USB
- **Conditional Breakpoints** — Data value matching, count triggers, task-specific stops
- **Deep Inspection** — Call stacks with locals, struct expansion, memory dumps
- **Any AI Agent** — Works with Claude Code, Codex, Qwen, or any MCP-compatible agent
- **Open Source** — MIT licensed, no restrictions

## License

MIT
