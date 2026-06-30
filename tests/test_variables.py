"""Tests for variable tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_variable_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.variable is not None


def test_variable_read_mock(connected_state, mock_debugger):
    mock_var = MagicMock()
    mock_var.name = "counter"
    mock_var.value = 42
    mock_debugger.variable.read.return_value = mock_var
    dbg = connected_state.require_connection()
    result = dbg.variable.read("counter")
    assert result.value == 42
