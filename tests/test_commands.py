"""Tests for command and scripting tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_cmd(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.cmd is not None


def test_cmd_callable(connected_state, mock_debugger):
    dbg = connected_state.require_connection()
    dbg.cmd("SYStem.Up")
    mock_debugger.cmd.assert_called_with("SYStem.Up")
