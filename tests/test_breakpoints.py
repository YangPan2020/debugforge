"""Tests for breakpoint tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_breakpoint_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.breakpoint is not None


def test_breakpoint_list_mock(connected_state, mock_debugger):
    mock_debugger.breakpoint.list.return_value = []
    dbg = connected_state.require_connection()
    result = dbg.breakpoint.list()
    assert result == []
