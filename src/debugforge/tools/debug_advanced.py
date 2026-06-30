"""Advanced execution and debug analysis tools for automated debugging."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def go_till(address: str) -> str:
    """Run until a specific address is reached (temporary breakpoint).

    Args:
        address: Target address or symbol to run to (e.g., "main", "0x80001000")

    Returns:
        State after reaching the address (or timeout info)
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"Go {address}")
        return f"Running to {address}..."
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error in go_till: {e}"


@mcp.tool()
async def go_up() -> str:
    """Run until the current function returns to its caller (step out).

    Returns:
        State after returning to caller
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Go.Up")
        return "Returned to caller function"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error in go_up: {e}"


@mcp.tool()
async def go_return() -> str:
    """Run to the last instruction of the current function (before return).

    Unlike go_up, this stops INSIDE the current function at its return point.

    Returns:
        State at function return point
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Go.Return")
        return "Stopped at function return point"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error in go_return: {e}"


@mcp.tool()
async def get_disassembly(address: str = "", lines: int = 30) -> str:
    """Get disassembly listing at an address (or current PC if not specified).

    Shows mixed source and assembly code for understanding what the CPU is executing.

    Args:
        address: Start address or symbol. Empty = current PC.
        lines: Approximate number of lines to return (default: 30)

    Returns:
        Disassembly listing with source code interleaved
    """
    dbg = state.require_connection()
    try:
        if address:
            cmd = f"Data.List {address}"
        else:
            cmd = "Data.List"
        result = _read_window(dbg, cmd, max_size=lines * 100)
        if not result.strip():
            return "No disassembly available (check address or symbols)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting disassembly: {e}"


@mcp.tool()
async def get_source_listing(address: str = "") -> str:
    """Get the source code listing around the current execution point.

    Shows HLL (C/C++) source with line numbers. The target must be halted.

    Args:
        address: Address or symbol. Empty = current PC.

    Returns:
        Source code listing
    """
    dbg = state.require_connection()
    try:
        if address:
            cmd = f"List.Hll {address}"
        else:
            cmd = "List.Hll"
        result = _read_window(dbg, cmd)
        if not result.strip():
            return "No source listing available (check debug symbols)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting source listing: {e}"


@mcp.tool()
async def var_set(name: str, value: str) -> str:
    """Set a C/C++ variable to a new value on the target.

    The target must be halted. Supports any assignable lvalue.

    Args:
        name: Variable name (e.g., "counter", "myStruct.field", "array[0]")
        value: New value as C expression (e.g., "42", "0xFF", "NULL")

    Returns:
        Confirmation of variable modification
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"Var.Set {name}={value}")
        return f"Variable set: {name} = {value}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting variable '{name}': {e}"


@mcp.tool()
async def get_task_list() -> str:
    """Get the list of OS tasks/threads (requires OS-awareness configured).

    Returns:
        Task list with names, IDs, states, and priorities
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "TASK.List")
        if not result.strip():
            return "No task list available (OS-awareness may not be configured)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting task list: {e}"


@mcp.tool()
async def get_task_stack(task: str = "") -> str:
    """Get stack information for OS tasks.

    Args:
        task: Task name or ID. Empty = all tasks.

    Returns:
        Task stack usage information
    """
    dbg = state.require_connection()
    try:
        cmd = f"TASK.STack {task}" if task else "TASK.STack"
        result = _read_window(dbg, cmd)
        if not result.strip():
            return "No task stack info available"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting task stack: {e}"


@mcp.tool()
async def get_peripheral_view(peripheral: str = "") -> str:
    """View peripheral register contents.

    Args:
        peripheral: Peripheral name or address. Empty = open general view.

    Returns:
        Peripheral register values
    """
    dbg = state.require_connection()
    try:
        cmd = f"PER.view {peripheral}" if peripheral else "PER.view"
        result = _read_window(dbg, cmd)
        if not result.strip():
            return "No peripheral data available"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting peripheral view: {e}"


@mcp.tool()
async def data_set(address: str, value: str, width: str = "long") -> str:
    """Write a value directly to a memory address using Data.Set.

    Args:
        address: Memory address (e.g., "D:0xF0036250", "0x80000000")
        value: Value to write (e.g., "0x00000008", "0xFF")
        width: Data width — "byte", "word" (16-bit), "long" (32-bit), "quad" (64-bit)

    Returns:
        Confirmation of write
    """
    dbg = state.require_connection()
    try:
        width_map = {"byte": "%Byte", "word": "%Word", "long": "%Long", "quad": "%Quad"}
        w = width_map.get(width, "%Long")
        dbg.cmd(f"Data.Set {address} {w} {value}")
        return f"Data.Set {address} {w} {value} — OK"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting data at {address}: {e}"
