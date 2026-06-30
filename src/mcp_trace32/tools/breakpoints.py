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
