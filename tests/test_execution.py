"""Tests for execution control tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_require_connection_needed(disconnected_state):
    with pytest.raises(ConnectionError, match="Not connected"):
        disconnected_state.require_connection()


def test_connected_state_has_cmd(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.cmd is not None
