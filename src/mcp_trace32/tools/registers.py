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
