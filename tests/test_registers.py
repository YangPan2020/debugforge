"""Tests for register tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_register_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.register is not None


def test_register_read_mock(connected_state, mock_debugger):
    mock_reg = MagicMock()
    mock_reg.name = "PC"
    mock_reg.value = 0x80001000
    mock_debugger.register.read.return_value = mock_reg
    dbg = connected_state.require_connection()
    result = dbg.register.read("PC")
    assert result.name == "PC"
    assert result.value == 0x80001000
