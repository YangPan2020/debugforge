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
        if addr_val is not None and addr_val != 0xFFFFFFFF:
            return f"Symbol '{name}': address = 0x{addr_val:08X}"
        else:
            return f"Symbol '{name}' not found (no matching debug symbol loaded)"
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
