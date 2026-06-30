"""Tests for memory tools."""

import pytest
from unittest.mock import MagicMock
from mcp_trace32.state import T32State


def test_connected_state_has_memory_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.memory is not None


def test_memory_read_mock(connected_state, mock_debugger):
    mock_debugger.memory.read.return_value = b'\x01\x02\x03\x04'
    dbg = connected_state.require_connection()
    result = dbg.memory.read(MagicMock(), length=4)
    assert result == b'\x01\x02\x03\x04'
