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


@mcp.tool()
async def capture_trap() -> str:
    """Capture complete trap/exception debug information in one call.

    When the CPU has stopped due to a trap/exception, this tool retrieves ALL
    relevant debug information at once without modifying any state:
      1. CPU state (running/halted, system mode)
      2. Key registers (PC, PSW, and architecture-specific registers)
      3. Current source location (function, file, line)
      4. Full call stack with locals and caller info
      5. Disassembly around the current PC

    This is a read-only operation — it does NOT reset, halt, or modify the
    target. Safe to call when the CPU is already stopped at a trap.

    Returns:
        Formatted trap analysis report with all debug information
    """
    dbg = state.require_connection()
    parts = ["# TRAP Capture Report", ""]

    # 1. CPU State
    parts.append("## CPU State")
    try:
        running = dbg.fnc.state_run()
        parts.append(f"  Running: {running}")
    except Exception:
        parts.append("  Running: (unknown)")
    try:
        sys_mode = dbg.fnc.system_mode()
        parts.append(f"  System Mode: {sys_mode}")
    except Exception:
        pass
    parts.append("")

    # 2. Registers — try common names across architectures
    #    TriCore: PC, PSW, A0-A15, D0-D15, FCX, LCX, ISP, ICR
    #    Cortex-M: PC, LR, SP, xPSR (silently skipped if not available)
    parts.append("## Registers")
    reg_names = [
        "PC", "PSW", "SP", "A0", "A1", "A2", "A3", "A4", "A5",
        "D0", "D1", "D2", "D3", "D4", "D5",
        "A10", "A11", "A12", "A13", "A14", "A15",
        "D10", "D11", "D12", "D13", "D14", "D15",
        "FCX", "LCX", "ISP", "ICR",
        "LR", "xPSR", "PCXI",
    ]
    reg_vals = {}
    for rn in reg_names:
        try:
            val = dbg.register.read(rn)
            v = val.value if hasattr(val, "value") else val
            reg_vals[rn] = v
            parts.append(f"  {rn:4s} = 0x{v:08X}")
        except Exception:
            pass
    parts.append("")

    pc_val = reg_vals.get("PC", 0)
    psw_val = reg_vals.get("PSW", 0)

    # 3. Source Location
    parts.append("## Source Location")
    try:
        dbg.cmd("EVAL sYmbol.FUNCtion(PP())")
        func_name = dbg.fnc.eval_string()
        parts.append(f"  Function: {func_name}")
    except Exception:
        parts.append("  Function: (unknown)")
    try:
        dbg.cmd("EVAL sYmbol.SOURCEFILE(PP())")
        src_file = dbg.fnc.eval_string()
        parts.append(f"  Source: {src_file}")
    except Exception:
        parts.append("  Source: (unknown)")
    try:
        dbg.cmd("EVAL sYmbol.SOURCELINE(PP())")
        src_line = str(dbg.fnc.eval())
        parts.append(f"  Line: {src_line}")
    except Exception:
        parts.append("  Line: (unknown)")
    parts.append("")

    # 4. Call Stack
    parts.append("## Call Stack")
    try:
        result = _read_window(dbg, "Frame.view /Locals /Caller")
        if result.strip():
            parts.append(result.strip())
        else:
            parts.append("  (empty)")
    except Exception as e:
        parts.append(f"  Error: {e}")
    parts.append("")

    # 5. Disassembly around PC
    parts.append("## Disassembly (PC +/- 0x40)")
    if pc_val:
        start = max(0, pc_val - 0x40)
        end = pc_val + 0x40
        try:
            result = _read_window(dbg, f"Data.List P:0x{start:08X}--0x{end:08X}")
            if result.strip():
                parts.append(result.strip())
            else:
                parts.append("  (no disassembly)")
        except Exception as e:
            parts.append(f"  Error: {e}")
    parts.append("")

    # 6. PSW analysis (best-effort, architecture-agnostic)
    if psw_val:
        parts.append("## PSW Analysis")
        io_bits = (psw_val >> 24) & 0xFF
        is_bits = (psw_val >> 16) & 0xFF
        cdc = (psw_val >> 8) & 0xFF
        parts.append(f"  PSW.IO = 0x{io_bits:02X}")
        parts.append(f"  PSW.IS = 0x{is_bits:02X}")
        parts.append(f"  PSW.CDC = 0x{cdc:02X}")
        parts.append("")

    parts.append("# End of TRAP Capture")
    return "\n".join(parts)


@mcp.tool()
async def read_string(address: str, max_length: int = 256) -> str:
    """Read a null-terminated string from target memory.

    Useful for reading assert filenames, error messages, or any C string
    stored in target memory.

    Args:
        address: Memory address as hex string (e.g., "0x808777A8") or with
                 access class prefix (e.g., "D:0x808777A8")
        max_length: Maximum bytes to read (default: 256)

    Returns:
        The string read from memory, or error message
    """
    dbg = state.require_connection()
    try:
        # Use TRACE32 window to read string via Data.dump /Byte
        result = _read_window(dbg, f"Data.dump {address}++0x{max_length - 1:X} /Byte")
        if not result.strip():
            return f"No data at {address}"

        # Parse the hex dump to extract ASCII string
        lines = result.strip().split("\n")
        ascii_chars = []
        for line in lines:
            # Find the ASCII portion after the | separator
            if "|" in line:
                ascii_part = line.split("|")[-1].rstrip("|")
                ascii_chars.append(ascii_part)

        full_ascii = "".join(ascii_chars)
        # Truncate at first null byte
        null_pos = full_ascii.find("\x00")
        if null_pos >= 0:
            full_ascii = full_ascii[:null_pos]

        return full_ascii if full_ascii else f"(empty string at {address})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading string at {address}: {e}"
