"""Advanced debug view tools for TRACE32 — call stack, locals, memory dump, variable inspection."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


def _read_window(dbg, command: str, max_size: int = 32768) -> str:
    """Read formatted content from a TRACE32 window via _get_window_content API."""
    content = bytearray()
    offset = 0
    while True:
        length, chunk = dbg._get_window_content(command, 4096, offset, "ASCII")
        if length == 0 or not chunk:
            break
        content += chunk[:length]
        offset += length
        if offset >= max_size:
            break
    return content.decode("utf-8", errors="replace")


@mcp.tool()
async def get_callstack() -> str:
    """Get the current call stack (backtrace) with function names and arguments.

    The target must be halted. Shows the complete call chain from the current
    function up to the entry point, including function arguments and source context.

    Returns:
        Formatted call stack with frame numbers, function names, and arguments
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "Frame.view /Caller")
        if not result.strip():
            return "Call stack empty (target may be running or no debug symbols loaded)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting call stack: {e}"


@mcp.tool()
async def get_locals() -> str:
    """Get the call stack with all local variables for each frame.

    The target must be halted. Shows local variable names and values for
    every function in the call stack. Useful for understanding program state
    at the point of a breakpoint or crash.

    Returns:
        Call stack with local variables expanded per frame
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "Frame.view /Locals /Caller")
        if not result.strip():
            return "No local variables available (target may be running or no debug symbols loaded)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting locals: {e}"


@mcp.tool()
async def get_data_dump(address: str, length: int = 256, width: int = 32) -> str:
    """Get a formatted memory dump (hex + ASCII) from the target.

    Similar to TRACE32's Data.dump window. Shows memory contents in the standard
    hex dump format with address, hex values, and ASCII representation.

    Args:
        address: Start address (e.g., "0xD0000000", "D:0x80000000")
        length: Number of bytes to dump (default: 256)
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)

    Returns:
        Formatted hex dump with addresses, hex values, and ASCII
    """
    dbg = state.require_connection()
    try:
        end_addr = int(address, 16) + length - 1 if address.startswith("0x") or address.startswith("0X") else 0
        if end_addr > 0:
            cmd = f"Data.dump {address}--0x{end_addr:X} /Long"
        else:
            cmd = f"Data.dump {address}++0x{length - 1:X} /Long"

        if width == 8:
            cmd = cmd.replace("/Long", "/Byte")
        elif width == 16:
            cmd = cmd.replace("/Long", "/Word")
        elif width == 64:
            cmd = cmd.replace("/Long", "/Quad")

        result = _read_window(dbg, cmd)
        if not result.strip():
            return f"No data at {address} (memory may not be accessible)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error dumping memory at {address}: {e}"


@mcp.tool()
async def var_view(expression: str) -> str:
    """View a C/C++ variable, structure, array, or expression with full expansion.

    Shows the complete content of complex data types including nested structs,
    arrays, and pointer targets. Much more detailed than read_variable.

    The target must be halted.

    Args:
        expression: C variable name, struct member, array, or expression
                   (e.g., "myStruct", "array[0]", "pTask->state", "%SpotLight")

    Returns:
        Formatted variable view showing all fields and values
    """
    dbg = state.require_connection()
    try:
        cmd = f"Var.view {expression}"
        result = _read_window(dbg, cmd)
        if not result.strip():
            return f"Variable '{expression}' not accessible (check symbol name or target state)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error viewing variable '{expression}': {e}"


@mcp.tool()
async def get_register_view() -> str:
    """Get the full register view with all CPU registers and flags.

    Shows all registers organized by type (data, address, system) with
    flags decoded. More comprehensive than read_register/read_registers.

    Returns:
        Complete formatted register dump including flags and special registers
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "Register.view")
        if not result.strip():
            return "Registers not accessible (target may be running)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting register view: {e}"


@mcp.tool()
async def get_window(command: str) -> str:
    """Get the text content of any TRACE32 window command.

    This is the most flexible view tool — any TRACE32 command that produces
    a window can have its content retrieved. Use this for specialized views
    not covered by other tools.

    Examples:
        - "Data.List" — disassembly listing
        - "Var.Watch" — variable watch window
        - "Frame.view /Locals /ALL" — all frames with locals
        - "Trace.List" — trace buffer contents
        - "TASK.List" — OS task/thread list

    Args:
        command: TRACE32 window command (e.g., "Data.List", "Var.Watch")

    Returns:
        Formatted text content of the specified window
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, command)
        if not result.strip():
            return f"Window '{command}' returned empty content"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting window content '{command}': {e}"
