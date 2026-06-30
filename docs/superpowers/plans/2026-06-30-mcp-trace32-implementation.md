# mcp-trace32 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MCP server that exposes Lauterbach TRACE32 debugger operations as 24 granular tools, allowing AI agents to perform hardware debugging via the standard MCP protocol.

**Architecture:** Modular FastMCP server with tool groups split by domain (connection, execution, memory, registers, breakpoints, variables, symbols, commands). Single global connection state shared across tools. stdio transport only.

**Tech Stack:** Python 3.10+, `mcp[cli]` (FastMCP), `lauterbach-trace32-rcl` (PYRCL v1.1.4), hatchling (build), pytest (tests)

---

## File Structure

```
mcp-trace32/
├── src/mcp_trace32/
│   ├── __init__.py            # Package version
│   ├── __main__.py            # python -m mcp_trace32 entry point
│   ├── server.py              # FastMCP instance, lifespan, register all tools
│   ├── state.py               # T32State dataclass holding Debugger connection
│   └── tools/
│       ├── __init__.py        # Empty, makes it a package
│       ├── connection.py      # connect, disconnect, status
│       ├── execution.py       # go, step, halt, reset, get_state
│       ├── memory.py          # read_memory, write_memory
│       ├── registers.py       # read_register, read_registers, write_register
│       ├── breakpoints.py     # set_breakpoint, list_breakpoints, delete_breakpoint, toggle_breakpoint
│       ├── variables.py       # read_variable, write_variable
│       ├── symbols.py         # symbol_by_name, symbol_by_address
│       └── commands.py        # execute_command, run_practice, evaluate
├── tests/
│   ├── conftest.py            # Shared fixtures (mock debugger, mock state)
│   ├── test_connection.py
│   ├── test_execution.py
│   ├── test_memory.py
│   ├── test_registers.py
│   ├── test_breakpoints.py
│   ├── test_variables.py
│   ├── test_symbols.py
│   └── test_commands.py
├── pyproject.toml             # Build config, dependencies, entry points
├── README.md
├── LICENSE
└── .github/
    └── workflows/
        └── ci.yml
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `README.md`
- Create: `src/mcp_trace32/__init__.py`
- Create: `src/mcp_trace32/__main__.py`
- Create: `src/mcp_trace32/tools/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mcp-trace32"
version = "0.1.0"
description = "MCP server for Lauterbach TRACE32 debugger — enables AI agents to perform hardware debugging"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "lixiang" },
]
keywords = ["mcp", "trace32", "lauterbach", "debugger", "embedded", "ai-agent"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Embedded Systems",
]
dependencies = [
    "mcp[cli]>=1.0.0",
    "lauterbach-trace32-rcl>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
]

[project.scripts]
mcp-trace32 = "mcp_trace32.server:main"

[project.urls]
Homepage = "https://github.com/lixiang/mcp-trace32"
Repository = "https://github.com/lixiang/mcp-trace32"
Issues = "https://github.com/lixiang/mcp-trace32/issues"
```

- [ ] **Step 2: Create LICENSE (MIT)**

```
MIT License

Copyright (c) 2026 lixiang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Create README.md**

```markdown
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
```

- [ ] **Step 4: Create src/mcp_trace32/__init__.py**

```python
"""MCP server for Lauterbach TRACE32 debugger."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Create src/mcp_trace32/__main__.py**

```python
"""Entry point for python -m mcp_trace32."""

from mcp_trace32.server import main

main()
```

- [ ] **Step 6: Create src/mcp_trace32/tools/__init__.py**

```python
"""TRACE32 MCP tool modules."""
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml LICENSE README.md src/
git commit -m "feat: project scaffolding with pyproject.toml, README, and package structure"
```

---

### Task 2: State Management

**Files:**
- Create: `src/mcp_trace32/state.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create state.py**

```python
"""Global connection state for the TRACE32 MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field

try:
    from lauterbach.trace32 import rcl as t32
    from lauterbach.trace32.rcl import Debugger
except ImportError:
    t32 = None
    Debugger = None


@dataclass
class T32State:
    """Holds the active TRACE32 connection and metadata."""

    debugger: Debugger | None = None
    node: str = ""
    port: int = 0
    protocol: str = ""

    @property
    def connected(self) -> bool:
        return self.debugger is not None

    def require_connection(self) -> Debugger:
        if self.debugger is None:
            raise ConnectionError(
                "Not connected to TRACE32. Call the 'connect' tool first."
            )
        return self.debugger

    async def connect(self, node: str = "localhost", port: int = 20000, protocol: str = "TCP") -> str:
        if self.debugger is not None:
            return f"Already connected to TRACE32 at {self.node}:{self.port}"

        if t32 is None:
            raise ImportError(
                "lauterbach-trace32-rcl package not installed. "
                "Install from your TRACE32 installation: "
                "pip install /opt/t32/demo/api/python/rcl/dist/lauterbach_trace32_rcl-*.whl"
            )

        self.debugger = t32.connect(node=node, port=port, protocol=protocol)
        self.node = node
        self.port = port
        self.protocol = protocol
        return f"Connected to TRACE32 at {node}:{port} via {protocol}"

    async def disconnect(self) -> str:
        if self.debugger is None:
            return "Not connected"
        self.debugger.disconnect()
        self.debugger = None
        node, port = self.node, self.port
        self.node = ""
        self.port = 0
        self.protocol = ""
        return f"Disconnected from TRACE32 at {node}:{port}"


# Global state instance
state = T32State()
```

- [ ] **Step 2: Create tests/conftest.py with mock fixtures**

```python
"""Shared test fixtures for mcp-trace32."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock, AsyncMock
import pytest

from mcp_trace32.state import T32State


class MockDebugger:
    """Mock PYRCL Debugger for testing without hardware."""

    def __init__(self):
        self.cmd = MagicMock()
        self.memory = MagicMock()
        self.register = MagicMock()
        self.variable = MagicMock()
        self.symbol = MagicMock()
        self.breakpoint = MagicMock()
        self.practice = MagicMock()
        self.fnc = MagicMock()
        self.address = MagicMock()

    def disconnect(self):
        pass


@pytest.fixture
def mock_debugger():
    """Provide a mock Debugger instance."""
    return MockDebugger()


@pytest.fixture
def connected_state(mock_debugger):
    """Provide a T32State that is already connected."""
    state = T32State()
    state.debugger = mock_debugger
    state.node = "localhost"
    state.port = 20000
    state.protocol = "TCP"
    return state


@pytest.fixture
def disconnected_state():
    """Provide a T32State with no connection."""
    return T32State()
```

- [ ] **Step 3: Run test to verify fixtures import correctly**

Run: `cd /home/lixiang/mywork/mcp-trace32 && python -c "from tests.conftest import MockDebugger; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/state.py tests/conftest.py
git commit -m "feat: add connection state management and test fixtures"
```

---

### Task 3: Server Core

**Files:**
- Create: `src/mcp_trace32/server.py`

- [ ] **Step 1: Create server.py**

```python
"""MCP server for TRACE32 debugger."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_trace32.state import state


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage server lifecycle — auto-connect if configured, cleanup on exit."""
    auto_connect = os.environ.get("T32_AUTO_CONNECT", "false").lower() == "true"
    if auto_connect:
        node = os.environ.get("T32_NODE", "localhost")
        port = int(os.environ.get("T32_PORT", "20000"))
        protocol = os.environ.get("T32_PROTOCOL", "TCP")
        try:
            await state.connect(node=node, port=port, protocol=protocol)
        except Exception:
            pass  # Non-fatal: user can connect manually via tool
    try:
        yield
    finally:
        if state.connected:
            await state.disconnect()


mcp = FastMCP(
    "mcp-trace32",
    description="MCP server for Lauterbach TRACE32 debugger — enables AI agents to perform hardware debugging",
    lifespan=lifespan,
)

# Import tool modules to register them on the mcp instance
from mcp_trace32.tools import connection  # noqa: E402, F401
from mcp_trace32.tools import execution  # noqa: E402, F401
from mcp_trace32.tools import memory  # noqa: E402, F401
from mcp_trace32.tools import registers  # noqa: E402, F401
from mcp_trace32.tools import breakpoints  # noqa: E402, F401
from mcp_trace32.tools import variables  # noqa: E402, F401
from mcp_trace32.tools import symbols  # noqa: E402, F401
from mcp_trace32.tools import commands  # noqa: E402, F401


def main():
    """Run the MCP server."""
    mcp.run()
```

- [ ] **Step 2: Commit**

```bash
git add src/mcp_trace32/server.py
git commit -m "feat: add FastMCP server core with lifespan and auto-connect"
```

---

### Task 4: Connection Tools

**Files:**
- Create: `src/mcp_trace32/tools/connection.py`
- Create: `tests/test_connection.py`

- [ ] **Step 1: Write tests for connection tools**

```python
"""Tests for connection tools."""

import pytest
from mcp_trace32.state import T32State


def test_state_not_connected_by_default(disconnected_state):
    assert disconnected_state.connected is False


def test_state_connected_after_attach(connected_state):
    assert connected_state.connected is True
    assert connected_state.node == "localhost"
    assert connected_state.port == 20000


def test_require_connection_raises_when_disconnected(disconnected_state):
    with pytest.raises(ConnectionError, match="Not connected"):
        disconnected_state.require_connection()


def test_require_connection_returns_debugger(connected_state, mock_debugger):
    dbg = connected_state.require_connection()
    assert dbg is mock_debugger


def test_disconnect_clears_state(connected_state):
    import asyncio
    result = asyncio.run(connected_state.disconnect())
    assert "Disconnected" in result
    assert connected_state.connected is False
    assert connected_state.node == ""
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /home/lixiang/mywork/mcp-trace32 && pip install -e ".[dev]" 2>/dev/null; pytest tests/test_connection.py -v`
Expected: All tests PASS

- [ ] **Step 3: Create connection tools**

```python
"""Connection management tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def connect(
    node: str = "localhost",
    port: int = 20000,
    protocol: str = "TCP",
) -> str:
    """Connect to a running TRACE32 PowerView instance.

    Args:
        node: TRACE32 host address (default: localhost)
        port: TRACE32 API port (default: 20000)
        protocol: Communication protocol - TCP or UDP (default: TCP)

    Returns:
        Connection status message with TRACE32 version info
    """
    try:
        result = await state.connect(node=node, port=port, protocol=protocol)
        try:
            dbg = state.require_connection()
            dbg.cmd("END")  # Clear any pending state
            version_str = ""
            try:
                dbg.cmd("EVAL SOFTWARE.VERSION()")
                import ctypes
                eval_string = ctypes.create_string_buffer(256)
                version_str = f" (version info available via 'status' tool)"
            except Exception:
                pass
            return result + version_str
        except Exception:
            return result
    except ImportError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Failed to connect to TRACE32 at {node}:{port} — {type(e).__name__}: {e}"


@mcp.tool()
async def disconnect() -> str:
    """Disconnect from TRACE32 PowerView.

    Returns:
        Disconnection confirmation message
    """
    return await state.disconnect()


@mcp.tool()
async def status() -> str:
    """Get current connection status and TRACE32 system information.

    Returns:
        Connection state, TRACE32 version, and target CPU state
    """
    if not state.connected:
        return "Status: Not connected to TRACE32"

    info_parts = [
        f"Status: Connected to TRACE32 at {state.node}:{state.port} ({state.protocol})",
    ]

    dbg = state.require_connection()
    try:
        dbg.cmd("EVAL SOFTWARE.VERSION()")
        from lauterbach.trace32.rcl import Debugger
        version = dbg.fnc.software_version()
        info_parts.append(f"TRACE32 Version: {version}")
    except Exception:
        info_parts.append("TRACE32 Version: (unable to query)")

    try:
        cpu_state = dbg.fnc.system_mode()
        info_parts.append(f"System Mode: {cpu_state}")
    except Exception:
        pass

    return "\n".join(info_parts)
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/connection.py tests/test_connection.py
git commit -m "feat: add connection tools (connect, disconnect, status)"
```

---

### Task 5: Execution Control Tools

**Files:**
- Create: `src/mcp_trace32/tools/execution.py`
- Create: `tests/test_execution.py`

- [ ] **Step 1: Write tests for execution tools**

```python
"""Tests for execution control tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_require_connection_needed(disconnected_state):
    with pytest.raises(ConnectionError, match="Not connected"):
        disconnected_state.require_connection()


def test_connected_state_has_cmd(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.cmd is not None
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_execution.py -v`
Expected: PASS

- [ ] **Step 3: Create execution tools**

```python
"""Execution control tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def go() -> str:
    """Start or continue program execution on the target.

    Returns:
        Confirmation that execution was started
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Go")
        return "Program execution started"
    except Exception as e:
        return f"Error starting execution: {e}"


@mcp.tool()
async def step(mode: str = "into") -> str:
    """Single-step program execution.

    Args:
        mode: Step mode — "into" (step into functions), "over" (step over),
              "out" (step out of current function)

    Returns:
        New program counter address after step
    """
    dbg = state.require_connection()
    cmd_map = {
        "into": "Step",
        "over": "Step.Over",
        "out": "Step.Out",
    }
    cmd = cmd_map.get(mode)
    if cmd is None:
        return f"Invalid step mode '{mode}'. Use: into, over, out"

    try:
        dbg.cmd(cmd)
        try:
            pc = dbg.fnc.register_pc()
            return f"Stepped ({mode}). PC = 0x{pc:08X}"
        except Exception:
            return f"Stepped ({mode}). Use 'read_register' to check PC."
    except Exception as e:
        return f"Error during step: {e}"


@mcp.tool()
async def halt() -> str:
    """Stop (break) program execution on the target.

    Returns:
        CPU state after halting
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Break")
        try:
            pc = dbg.fnc.register_pc()
            return f"Execution halted. PC = 0x{pc:08X}"
        except Exception:
            return "Execution halted"
    except Exception as e:
        return f"Error halting execution: {e}"


@mcp.tool()
async def reset() -> str:
    """Reset the target CPU.

    Returns:
        Confirmation of reset
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("SYStem.RESetTarget")
        return "Target reset complete"
    except Exception as e:
        return f"Error resetting target: {e}"


@mcp.tool()
async def get_state() -> str:
    """Get the current CPU/target execution state.

    Returns:
        Current state: running, stopped, power-down, or other system state
    """
    dbg = state.require_connection()
    try:
        sys_mode = dbg.fnc.system_mode()
        info = f"System mode: {sys_mode}"
        try:
            run_state = dbg.fnc.state_run()
            if run_state:
                info += "\nCPU: Running"
            else:
                pc = dbg.fnc.register_pc()
                info += f"\nCPU: Stopped at PC = 0x{pc:08X}"
        except Exception:
            pass
        return info
    except Exception as e:
        return f"Error getting state: {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/execution.py tests/test_execution.py
git commit -m "feat: add execution control tools (go, step, halt, reset, get_state)"
```

---

### Task 6: Memory Tools

**Files:**
- Create: `src/mcp_trace32/tools/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write tests for memory tools**

```python
"""Tests for memory tools."""

import pytest
from unittest.mock import MagicMock, patch
from mcp_trace32.state import T32State


def test_connected_state_has_memory_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.memory is not None


def test_memory_read_mock(connected_state, mock_debugger):
    mock_debugger.memory.read.return_value = b'\x01\x02\x03\x04'
    dbg = connected_state.require_connection()
    result = dbg.memory.read(MagicMock(), length=4)
    assert result == b'\x01\x02\x03\x04'
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_memory.py -v`
Expected: PASS

- [ ] **Step 3: Create memory tools**

```python
"""Memory access tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def read_memory(
    address: str,
    length: int,
    width: int = 32,
    access: str = "",
) -> str:
    """Read memory from the target at a given address.

    Args:
        address: Memory address as hex string (e.g., "0x80000000") or symbol name (e.g., "main")
        length: Number of bytes to read
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)
        access: Access class prefix (e.g., "D:" for data, "P:" for program). Empty = default.

    Returns:
        Hex dump of memory contents
    """
    dbg = state.require_connection()
    try:
        addr_str = f"{access}{address}" if access else address
        addr = dbg.address.from_string(addr_str)
        data = dbg.memory.read(addr, length=length, width=width // 8 if width > 8 else None)

        # Format as hex dump
        hex_lines = []
        bytes_per_line = 16
        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            addr_val = int(address, 16) + offset if address.startswith("0x") or address.startswith("0X") else offset
            hex_lines.append(f"0x{addr_val:08X}: {hex_part:<48s} |{ascii_part}|")

        return "\n".join(hex_lines) if hex_lines else "No data read"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading memory at {address}: {e}"


@mcp.tool()
async def write_memory(
    address: str,
    data: str,
    width: int = 32,
    access: str = "",
) -> str:
    """Write data to target memory at a given address.

    Args:
        address: Memory address as hex string (e.g., "0x80000000") or symbol name
        data: Hex string of bytes to write (e.g., "DEADBEEF" for 4 bytes)
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)
        access: Access class prefix (e.g., "D:" for data). Empty = default.

    Returns:
        Confirmation with number of bytes written
    """
    dbg = state.require_connection()
    try:
        addr_str = f"{access}{address}" if access else address
        addr = dbg.address.from_string(addr_str)
        byte_data = bytes.fromhex(data)
        dbg.memory.write(addr, byte_data, width=width // 8 if width > 8 else None)
        return f"Wrote {len(byte_data)} bytes to {address}"
    except ConnectionError:
        raise
    except ValueError as e:
        return f"Invalid hex data '{data}': {e}"
    except Exception as e:
        return f"Error writing memory at {address}: {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/memory.py tests/test_memory.py
git commit -m "feat: add memory tools (read_memory, write_memory)"
```

---

### Task 7: Register Tools

**Files:**
- Create: `src/mcp_trace32/tools/registers.py`
- Create: `tests/test_registers.py`

- [ ] **Step 1: Write tests for register tools**

```python
"""Tests for register tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_register_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.register is not None


def test_register_read_mock(connected_state, mock_debugger):
    mock_reg = MagicMock()
    mock_reg.name = "PC"
    mock_reg.value = 0x80001000
    mock_debugger.register.read.return_value = mock_reg
    dbg = connected_state.require_connection()
    result = dbg.register.read("PC")
    assert result.name == "PC"
    assert result.value == 0x80001000
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_registers.py -v`
Expected: PASS

- [ ] **Step 3: Create register tools**

```python
"""Register access tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def read_register(name: str) -> str:
    """Read a single CPU register by name.

    Args:
        name: Register name (e.g., "PC", "SP", "R0", "D0", "A0")

    Returns:
        Register name and its current value
    """
    dbg = state.require_connection()
    try:
        reg = dbg.register.read(name)
        value = reg.value
        if isinstance(value, int):
            return f"{reg.name} = 0x{value:08X} ({value})"
        else:
            return f"{reg.name} = {value}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading register '{name}': {e}"


@mcp.tool()
async def read_registers(names: list[str] | None = None, core: str = "") -> str:
    """Read multiple CPU registers.

    Args:
        names: List of register names to read. If empty/None, reads all registers.
        core: Filter by core/unit (e.g., "CPU", "FPU"). Empty = all.

    Returns:
        Table of register names and values
    """
    dbg = state.require_connection()
    try:
        if names:
            regs = dbg.register.read_by_names(names)
        else:
            kwargs = {}
            if core:
                kwargs["unit"] = core
            regs = dbg.register.read_all(**kwargs)

        lines = []
        for reg in regs:
            value = reg.value
            if isinstance(value, int):
                lines.append(f"  {reg.name:<12s} = 0x{value:08X} ({value})")
            else:
                lines.append(f"  {reg.name:<12s} = {value}")

        header = f"Registers ({len(regs)}):"
        return header + "\n" + "\n".join(lines) if lines else "No registers found"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading registers: {e}"


@mcp.tool()
async def write_register(name: str, value: int) -> str:
    """Write a value to a CPU register.

    Args:
        name: Register name (e.g., "PC", "SP", "R0")
        value: Integer value to write

    Returns:
        Confirmation with the register's new value
    """
    dbg = state.require_connection()
    try:
        reg = dbg.register.write(name, value)
        return f"Written: {reg.name} = 0x{value:08X} ({value})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error writing register '{name}': {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/registers.py tests/test_registers.py
git commit -m "feat: add register tools (read_register, read_registers, write_register)"
```

---

### Task 8: Breakpoint Tools

**Files:**
- Create: `src/mcp_trace32/tools/breakpoints.py`
- Create: `tests/test_breakpoints.py`

- [ ] **Step 1: Write tests for breakpoint tools**

```python
"""Tests for breakpoint tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_breakpoint_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.breakpoint is not None


def test_breakpoint_list_mock(connected_state, mock_debugger):
    mock_debugger.breakpoint.list.return_value = []
    dbg = connected_state.require_connection()
    result = dbg.breakpoint.list()
    assert result == []
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_breakpoints.py -v`
Expected: PASS

- [ ] **Step 3: Create breakpoint tools**

```python
"""Breakpoint management tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def set_breakpoint(
    address: str,
    type: str = "program",
    impl: str = "auto",
) -> str:
    """Set a breakpoint at the specified address or symbol.

    Args:
        address: Address (hex e.g. "0x80001000") or symbol name (e.g. "main")
        type: Breakpoint type — "program", "read", "write", or "readwrite"
        impl: Implementation — "auto", "soft" (software), or "hard" (hardware)

    Returns:
        Breakpoint details confirming the set operation
    """
    dbg = state.require_connection()
    try:
        type_map = {
            "program": "Program",
            "read": "Read",
            "write": "Write",
            "readwrite": "ReadWrite",
        }
        bp_type = type_map.get(type)
        if bp_type is None:
            return f"Invalid breakpoint type '{type}'. Use: program, read, write, readwrite"

        impl_map = {
            "auto": "",
            "soft": "/Soft",
            "hard": "/Onchip",
        }
        bp_impl = impl_map.get(impl, "")

        cmd = f"Break.Set {address} /{bp_type}{bp_impl}"
        dbg.cmd(cmd)
        return f"Breakpoint set: {type} @ {address} ({impl})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting breakpoint at {address}: {e}"


@mcp.tool()
async def list_breakpoints() -> str:
    """List all active breakpoints.

    Returns:
        Table of all breakpoints with address, type, and state
    """
    dbg = state.require_connection()
    try:
        bps = dbg.breakpoint.list()
        if not bps:
            return "No breakpoints set"

        lines = ["Breakpoints:"]
        for i, bp in enumerate(bps):
            addr = bp.address
            addr_str = f"0x{addr.value:08X}" if addr and addr.value else "?"
            enabled = "enabled" if bp.enabled else "disabled"
            bp_type = str(bp.type_) if bp.type_ else "program"
            lines.append(f"  [{i}] {addr_str} — {bp_type} ({enabled})")

        return "\n".join(lines)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error listing breakpoints: {e}"


@mcp.tool()
async def delete_breakpoint(address: str) -> str:
    """Delete a breakpoint at the specified address.

    Args:
        address: Address or symbol name of the breakpoint to delete

    Returns:
        Confirmation of deletion
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"Break.Delete {address}")
        return f"Breakpoint deleted at {address}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error deleting breakpoint at {address}: {e}"


@mcp.tool()
async def toggle_breakpoint(address: str, enabled: bool) -> str:
    """Enable or disable a breakpoint without deleting it.

    Args:
        address: Address or symbol name of the breakpoint
        enabled: True to enable, False to disable

    Returns:
        New breakpoint state
    """
    dbg = state.require_connection()
    try:
        if enabled:
            dbg.cmd(f"Break.Enable {address}")
            return f"Breakpoint at {address} enabled"
        else:
            dbg.cmd(f"Break.Disable {address}")
            return f"Breakpoint at {address} disabled"
    except ConnectionError:
        raise
    except Exception as e:
        action = "enabling" if enabled else "disabling"
        return f"Error {action} breakpoint at {address}: {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/breakpoints.py tests/test_breakpoints.py
git commit -m "feat: add breakpoint tools (set, list, delete, toggle)"
```

---

### Task 9: Variable Tools

**Files:**
- Create: `src/mcp_trace32/tools/variables.py`
- Create: `tests/test_variables.py`

- [ ] **Step 1: Write tests for variable tools**

```python
"""Tests for variable tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_variable_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.variable is not None


def test_variable_read_mock(connected_state, mock_debugger):
    mock_var = MagicMock()
    mock_var.name = "counter"
    mock_var.value = 42
    mock_debugger.variable.read.return_value = mock_var
    dbg = connected_state.require_connection()
    result = dbg.variable.read("counter")
    assert result.value == 42
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_variables.py -v`
Expected: PASS

- [ ] **Step 3: Create variable tools**

```python
"""C/C++ variable access tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def read_variable(name: str) -> str:
    """Read a C/C++ variable from the target by its symbol name.

    The target must be halted (stopped) for variable reads to work.

    Args:
        name: Variable name as it appears in source code (e.g., "counter", "myStruct.field")

    Returns:
        Variable name and its current value
    """
    dbg = state.require_connection()
    try:
        var = dbg.variable.read(name)
        return f"{var.name} = {var.value}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading variable '{name}': {e}"


@mcp.tool()
async def write_variable(name: str, value: str) -> str:
    """Write a value to a C/C++ variable on the target.

    The target must be halted (stopped) for variable writes to work.

    Args:
        name: Variable name as it appears in source code
        value: Value to write (integer, float, or string representation)

    Returns:
        Confirmation with the new value
    """
    dbg = state.require_connection()
    try:
        # Try integer first, then float, then pass as string
        try:
            write_val = int(value, 0)  # Supports 0x hex, 0b binary, 0o octal
        except ValueError:
            try:
                write_val = float(value)
            except ValueError:
                write_val = value

        var = dbg.variable.write(name, write_val)
        return f"Written: {var.name} = {var.value}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error writing variable '{name}': {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/variables.py tests/test_variables.py
git commit -m "feat: add variable tools (read_variable, write_variable)"
```

---

### Task 10: Symbol Tools

**Files:**
- Create: `src/mcp_trace32/tools/symbols.py`
- Create: `tests/test_symbols.py`

- [ ] **Step 1: Write tests for symbol tools**

```python
"""Tests for symbol tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_symbol_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.symbol is not None


def test_symbol_query_by_name_mock(connected_state, mock_debugger):
    mock_sym = MagicMock()
    mock_sym.name = "main"
    mock_sym.address = MagicMock()
    mock_sym.address.value = 0x80001000
    mock_debugger.symbol.query_by_name.return_value = mock_sym
    dbg = connected_state.require_connection()
    result = dbg.symbol.query_by_name("main")
    assert result.name == "main"
    assert result.address.value == 0x80001000
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_symbols.py -v`
Expected: PASS

- [ ] **Step 3: Create symbol tools**

```python
"""Symbol lookup tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def symbol_by_name(name: str) -> str:
    """Look up a debug symbol by its name to get its address.

    Args:
        name: Symbol name (function, variable, label — e.g., "main", "g_counter")

    Returns:
        Symbol address and access info
    """
    dbg = state.require_connection()
    try:
        sym = dbg.symbol.query_by_name(name)
        addr = sym.address
        addr_val = addr.value if addr else None
        if addr_val is not None:
            return f"Symbol '{name}': address = 0x{addr_val:08X}"
        else:
            return f"Symbol '{name}' found but address unavailable"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Symbol '{name}' not found: {e}"


@mcp.tool()
async def symbol_by_address(address: str) -> str:
    """Look up a debug symbol by its address to get its name.

    Args:
        address: Memory address as hex string (e.g., "0x80001000")

    Returns:
        Symbol name at or near the given address
    """
    dbg = state.require_connection()
    try:
        addr = dbg.address.from_string(address)
        sym = dbg.symbol.query_by_address(addr)
        return f"Address {address}: symbol = '{sym.name}'"
    except ConnectionError:
        raise
    except Exception as e:
        return f"No symbol found at {address}: {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/symbols.py tests/test_symbols.py
git commit -m "feat: add symbol tools (symbol_by_name, symbol_by_address)"
```

---

### Task 11: Command & Scripting Tools

**Files:**
- Create: `src/mcp_trace32/tools/commands.py`
- Create: `tests/test_commands.py`

- [ ] **Step 1: Write tests for command tools**

```python
"""Tests for command and scripting tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_cmd(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.cmd is not None


def test_cmd_callable(connected_state, mock_debugger):
    dbg = connected_state.require_connection()
    dbg.cmd("SYStem.Up")
    mock_debugger.cmd.assert_called_with("SYStem.Up")
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_commands.py -v`
Expected: PASS

- [ ] **Step 3: Create command tools**

```python
"""Command execution and scripting tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def execute_command(command: str) -> str:
    """Execute any TRACE32 PRACTICE command string.

    This is the most flexible tool — any command you can type in the TRACE32
    command line can be executed here (e.g., "SYStem.Up", "Data.LOAD.Elf ...",
    "Break.Set main", "Var.View myVar").

    Args:
        command: TRACE32 command string to execute

    Returns:
        Success confirmation or error message from TRACE32
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(command)
        return f"Command executed: {command}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Command failed '{command}': {e}"


@mcp.tool()
async def run_practice(script: str, timeout: float = 60.0) -> str:
    """Run a PRACTICE (.cmm) script and wait for it to complete.

    Args:
        script: Path to the .cmm script file (absolute or relative to TRACE32)
        timeout: Maximum time to wait for script completion in seconds (default: 60)

    Returns:
        Script execution result (success or error message)
    """
    dbg = state.require_connection()
    try:
        dbg.cmm(f"DO {script}", timeout=timeout)
        return f"PRACTICE script completed: {script}"
    except TimeoutError:
        return f"PRACTICE script timed out after {timeout}s: {script}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"PRACTICE script error '{script}': {e}"


@mcp.tool()
async def evaluate(expression: str) -> str:
    """Evaluate a TRACE32 PRACTICE function or expression.

    Useful for querying system state, hardware info, or computing values.
    Examples: "SOFTWARE.VERSION()", "REGISTER(PC)", "sYmbol.BEGIN(main)"

    Args:
        expression: TRACE32 PRACTICE function or expression to evaluate

    Returns:
        Evaluation result as a string
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"EVAL {expression}")
        try:
            result = dbg.fnc.eval_string()
            return f"Result: {result}"
        except Exception:
            try:
                result = dbg.fnc.eval_int()
                return f"Result: {result} (0x{result:X})"
            except Exception:
                return f"Expression evaluated (use 'execute_command' with PRINT for string results)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Evaluation error '{expression}': {e}"
```

- [ ] **Step 4: Commit**

```bash
git add src/mcp_trace32/tools/commands.py tests/test_commands.py
git commit -m "feat: add command tools (execute_command, run_practice, evaluate)"
```

---

### Task 12: CI Configuration & Final Polish

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
```

- [ ] **Step 2: Create CI workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          # Install mock for lauterbach package (not available in CI)
          pip install unittest-mock

      - name: Run tests
        run: pytest tests/ -v --tb=short

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ruff
        run: pip install ruff

      - name: Lint
        run: ruff check src/ tests/

      - name: Format check
        run: ruff format --check src/ tests/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore .github/
git commit -m "chore: add .gitignore and GitHub Actions CI workflow"
```

---

### Task 13: Integration Verification

**Files:**
- None new — verify existing code works together

- [ ] **Step 1: Install the package locally in editable mode**

Run: `cd /home/lixiang/mywork/mcp-trace32 && pip install -e ".[dev]"`
Expected: Successful install (PYRCL may warn if not installed, that's OK)

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Verify MCP server starts (will fail to import pyrcl but should not crash)**

Run: `timeout 3 mcp-trace32 2>&1 || true`
Expected: Server starts and waits for stdio input (or graceful error about pyrcl)

- [ ] **Step 4: Verify package metadata**

Run: `python -c "import mcp_trace32; print(mcp_trace32.__version__)"`
Expected: `0.1.0`

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: integration fixes from verification"
```

(Skip if no fixes needed)
