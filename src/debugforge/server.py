"""MCP server for TRACE32 debugger."""

from __future__ import annotations

from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from debugforge.state import config, state


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage server lifecycle — auto-connect if configured, cleanup on exit."""
    if config.auto_connect:
        try:
            await state.connect(
                node=config.node, port=config.port, protocol=config.protocol
            )
        except Exception:
            pass
    try:
        yield
    finally:
        if state.connected:
            await state.disconnect()


mcp = FastMCP(
    "debugforge",
    instructions="DebugForge — MCP server bridging Lauterbach TRACE32 to AI agents. 47 tools for autonomous debugging: connect to target, inspect state, locate bugs, and drive fixes.",
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
