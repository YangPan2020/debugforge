"""Tests for DebugForge configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from debugforge.config import DebugForgeConfig, load_config


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Helper to write a config file and set CWD."""
    def _write(content: str) -> Path:
        config_file = tmp_path / "debugforge.toml"
        config_file.write_text(content)
        monkeypatch.chdir(tmp_path)
        return config_file
    return _write


class TestLoadConfigDefaults:
    def test_no_config_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        monkeypatch.delenv("T32_INSTALL_PATH", raising=False)
        monkeypatch.delenv("T32_NODE", raising=False)
        monkeypatch.delenv("T32_PORT", raising=False)
        monkeypatch.delenv("T32_PROTOCOL", raising=False)
        monkeypatch.delenv("T32_AUTO_CONNECT", raising=False)

        cfg = load_config()
        assert cfg.node == "localhost"
        assert cfg.port == 20000
        assert cfg.protocol == "TCP"
        assert cfg.auto_connect is False
        assert cfg.t32_install_path == ""
        assert cfg.elf == ""
        assert cfg.map == ""
        assert cfg.scripts == {}

    def test_backward_compatible_with_no_config(self, tmp_path, monkeypatch):
        """Existing behavior should be preserved when no config file exists."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        monkeypatch.delenv("T32_INSTALL_PATH", raising=False)
        monkeypatch.delenv("T32_NODE", raising=False)
        monkeypatch.delenv("T32_PORT", raising=False)
        monkeypatch.delenv("T32_PROTOCOL", raising=False)
        monkeypatch.delenv("T32_AUTO_CONNECT", raising=False)

        cfg = load_config()
        assert isinstance(cfg, DebugForgeConfig)


class TestLoadConfigFromFile:
    def test_loads_trace32_section(self, tmp_config):
        tmp_config('[trace32]\ninstall_path = "/opt/t32"')
        cfg = load_config()
        assert cfg.t32_install_path == "/opt/t32"

    def test_loads_connection_section(self, tmp_config):
        tmp_config(
            '[connection]\nnode = "192.168.1.100"\nport = 30000\n'
            'protocol = "UDP"\nauto_connect = true'
        )
        cfg = load_config()
        assert cfg.node == "192.168.1.100"
        assert cfg.port == 30000
        assert cfg.protocol == "UDP"
        assert cfg.auto_connect is True

    def test_loads_project_section(self, tmp_config, tmp_path):
        tmp_config('[project]\nelf = "build/app.elf"\nmap = "build/app.map"')
        cfg = load_config()
        assert cfg.elf == str(tmp_path / "build/app.elf")
        assert cfg.map == str(tmp_path / "build/app.map")

    def test_loads_scripts_section(self, tmp_config, tmp_path):
        tmp_config('[scripts]\nflash = "scripts/flash.cmm"\ninit = "scripts/init.cmm"')
        cfg = load_config()
        assert cfg.scripts["flash"] == str(tmp_path / "scripts/flash.cmm")
        assert cfg.scripts["init"] == str(tmp_path / "scripts/init.cmm")

    def test_relative_paths_resolved_from_config_dir(self, tmp_config, tmp_path):
        tmp_config('[project]\nelf = "output/fw.elf"')
        cfg = load_config()
        assert cfg.elf == str(tmp_path / "output/fw.elf")

    def test_absolute_paths_kept_as_is(self, tmp_config):
        tmp_config('[project]\nelf = "/absolute/path/fw.elf"')
        cfg = load_config()
        assert cfg.elf == "/absolute/path/fw.elf"


class TestEnvVarOverrides:
    def test_env_overrides_file_values(self, tmp_config, monkeypatch):
        tmp_config('[connection]\nnode = "from-file"\nport = 10000')
        monkeypatch.setenv("T32_NODE", "from-env")
        monkeypatch.setenv("T32_PORT", "55555")
        cfg = load_config()
        assert cfg.node == "from-env"
        assert cfg.port == 55555

    def test_t32_install_path_env(self, tmp_config, monkeypatch):
        tmp_config('[trace32]\ninstall_path = "/from/file"')
        monkeypatch.setenv("T32_INSTALL_PATH", "/from/env")
        cfg = load_config()
        assert cfg.t32_install_path == "/from/env"

    def test_auto_connect_env(self, tmp_config, monkeypatch):
        tmp_config('[connection]\nauto_connect = false')
        monkeypatch.setenv("T32_AUTO_CONNECT", "true")
        cfg = load_config()
        assert cfg.auto_connect is True

    def test_env_without_config_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        monkeypatch.setenv("T32_NODE", "myhost")
        monkeypatch.setenv("T32_PORT", "9999")
        cfg = load_config()
        assert cfg.node == "myhost"
        assert cfg.port == 9999


class TestExplicitConfigPath:
    def test_explicit_path_argument(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        monkeypatch.delenv("T32_NODE", raising=False)
        config_file = tmp_path / "custom.toml"
        config_file.write_text('[connection]\nnode = "custom-host"')
        cfg = load_config(config_path=str(config_file))
        assert cfg.node == "custom-host"

    def test_debugforge_config_env(self, tmp_path, monkeypatch):
        config_file = tmp_path / "alt.toml"
        config_file.write_text('[connection]\nport = 12345')
        monkeypatch.setenv("DEBUGFORGE_CONFIG", str(config_file))
        monkeypatch.delenv("T32_PORT", raising=False)
        cfg = load_config()
        assert cfg.port == 12345
