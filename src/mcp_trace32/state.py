"""Global connection state for the TRACE32 MCP server."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from lauterbach.trace32 import rcl as t32
    from lauterbach.trace32.rcl import Debugger
except ImportError:
    t32 = None
    Debugger = None


@dataclass
class T32State:
    """Holds the active TRACE32 connection and metadata."""

    debugger: object | None = None
    node: str = ""
    port: int = 0
    protocol: str = ""

    @property
    def connected(self) -> bool:
        return self.debugger is not None

    def require_connection(self):
        if self.debugger is None:
            raise ConnectionError(
                "Not connected to TRACE32. Call the 'connect' tool first."
            )
        return self.debugger

    async def connect(self, node: str = "localhost", port: int = 20000, protocol: str = "TCP") -> str:
        if self.debugger is not None:
            return f"Already connected to TRACE32 at {self.node}:{self.port}"

        if t32 is None:
            raise ImportError(
                "lauterbach-trace32-rcl package not installed. "
                "Install from your TRACE32 installation: "
                "pip install /opt/t32/demo/api/python/rcl/dist/lauterbach_trace32_rcl-*.whl"
            )

        self.debugger = t32.connect(node=node, port=port, protocol=protocol)
        self.node = node
        self.port = port
        self.protocol = protocol
        return f"Connected to TRACE32 at {node}:{port} via {protocol}"

    async def disconnect(self) -> str:
        if self.debugger is None:
            return "Not connected"
        self.debugger.disconnect()
        self.debugger = None
        node, port = self.node, self.port
        self.node = ""
        self.port = 0
        self.protocol = ""
        return f"Disconnected from TRACE32 at {node}:{port}"


state = T32State()
