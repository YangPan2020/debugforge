"""Tests for connection tools."""

import asyncio
import pytest
from mcp_trace32.state import T32State


def test_state_not_connected_by_default(disconnected_state):
    assert disconnected_state.connected is False


def test_state_connected_after_attach(connected_state):
    assert connected_state.connected is True
    assert connected_state.node == "localhost"
    assert connected_state.port == 20000


def test_require_connection_raises_when_disconnected(disconnected_state):
    with pytest.raises(ConnectionError, match="Not connected"):
        disconnected_state.require_connection()


def test_require_connection_returns_debugger(connected_state, mock_debugger):
    dbg = connected_state.require_connection()
    assert dbg is mock_debugger


def test_disconnect_clears_state(connected_state):
    result = asyncio.run(connected_state.disconnect())
    assert "Disconnected" in result
    assert connected_state.connected is False
    assert connected_state.node == ""
