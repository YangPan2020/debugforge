"""MCP server for TRACE32 debugger."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from debugforge.state import state


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
            pass
    try:
        yield
    finally:
        if state.connected:
            await state.disconnect()


mcp = FastMCP(
    "debugforge",
    instructions="DebugForge — AI-powered debugging for Lauterbach TRACE32. 46 tools for complete hardware debug automation.",
    lifespan=lifespan,
)

from debugforge.tools import connection  # noqa: E402, F401
from debugforge.tools import execution  # noqa: E402, F401
from debugforge.tools import memory  # noqa: E402, F401
from debugforge.tools import registers  # noqa: E402, F401
from debugforge.tools import breakpoints  # noqa: E402, F401
from debugforge.tools import variables  # noqa: E402, F401
from debugforge.tools import symbols  # noqa: E402, F401
from debugforge.tools import commands  # noqa: E402, F401
from debugforge.tools import views  # noqa: E402, F401
from debugforge.tools import breakpoints_advanced  # noqa: E402, F401
from debugforge.tools import debug_advanced  # noqa: E402, F401


def main():
    """Run the MCP server."""
    mcp.run()
