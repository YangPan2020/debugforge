"""Shared test fixtures for debugforge."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from debugforge.state import T32State


class MockDebugger:
    """Mock PYRCL Debugger for testing without hardware."""

    def __init__(self):
        self.cmd = MagicMock()
        self.memory = MagicMock()
        self.register = MagicMock()
        self.variable = MagicMock()
        self.symbol = MagicMock()
        self.breakpoint = MagicMock()
        self.practice = MagicMock()
        self.fnc = MagicMock()
        self.address = MagicMock()

    def disconnect(self):
        pass


@pytest.fixture
def mock_debugger():
    return MockDebugger()


@pytest.fixture
def connected_state(mock_debugger):
    s = T32State()
    s.debugger = mock_debugger
    s.node = "localhost"
    s.port = 20000
    s.protocol = "TCP"
    return s


@pytest.fixture
def disconnected_state():
    return T32State()
