"""Connection management tools for TRACE32."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import config, state


@mcp.tool()
async def connect(
    node: str = "",
    port: int = 0,
    protocol: str = "",
) -> str:
    """Connect to a running TRACE32 PowerView instance.

    Args:
        node: TRACE32 host address (default from config or 'localhost')
        port: TRACE32 API port (default from config or 20000)
        protocol: Communication protocol - TCP or UDP (default from config or 'TCP')

    Returns:
        Connection status message with TRACE32 version info
    """
    node = node or config.node
    port = port or config.port
    protocol = protocol or config.protocol
    try:
        result = await state.connect(node=node, port=port, protocol=protocol)
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
        version = dbg.fnc.software_version()
        info_parts.append(f"TRACE32 Version: {version}")
    except Exception:
        info_parts.append("TRACE32 Version: (unable to query)")

    try:
        sys_mode = dbg.fnc.system_mode()
        info_parts.append(f"System Mode: {sys_mode}")
    except Exception:
        pass

    return "\n".join(info_parts)
