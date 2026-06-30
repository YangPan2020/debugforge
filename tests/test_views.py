"""Tests for advanced view tools."""

import pytest
from unittest.mock import MagicMock
from debugforge.state import T32State


def test_connected_state_has_get_window_content(connected_state, mock_debugger):
    mock_debugger._get_window_content = MagicMock(return_value=(0, bytearray()))
    dbg = connected_state.require_connection()
    assert hasattr(dbg, '_get_window_content')


def test_window_content_returns_tuple(connected_state, mock_debugger):
    mock_debugger._get_window_content = MagicMock(
        return_value=(11, bytearray(b'Hello World'))
    )
    dbg = connected_state.require_connection()
    length, data = dbg._get_window_content('Test', 4096, 0, 'ASCII')
    assert length == 11
    assert data == bytearray(b'Hello World')
