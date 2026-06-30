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
        try:
            write_val: int | float | str = int(value, 0)
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
