"""Tests for symbol tools."""

import pytest
from unittest.mock import MagicMock
from debugforge.state import T32State


def test_connected_state_has_symbol_service(connected_state):
    dbg = connected_state.require_connection()
    assert dbg.symbol is not None


def test_symbol_query_by_name_mock(connected_state, mock_debugger):
    mock_sym = MagicMock()
    mock_sym.name = "main"
    mock_sym.address = MagicMock()
    mock_sym.address.value = 0x80001000
    mock_debugger.symbol.query_by_name.return_value = mock_sym
    dbg = connected_state.require_connection()
    result = dbg.symbol.query_by_name("main")
    assert result.name == "main"
    assert result.address.value == 0x80001000
