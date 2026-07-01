"""Tests for build integration tools."""

from __future__ import annotations

import pytest

from debugforge.config import load_config


class TestBuildConfig:
    def test_loads_build_section(self, tmp_path, monkeypatch):
        config_file = tmp_path / "debugforge.toml"
        config_file.write_text(
            '[build]\ncommand = "make -j4"\n'
            'clean_command = "make clean"\n'
            'working_dir = "build"'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.build_command == "make -j4"
        assert cfg.clean_command == "make clean"
        assert cfg.build_working_dir == str(tmp_path / "build")

    def test_loads_toolchain_section(self, tmp_path, monkeypatch):
        config_file = tmp_path / "debugforge.toml"
        config_file.write_text(
            '[toolchain]\n'
            'compiler_path = "/opt/gcc/bin"\n'
            'objdump = "arm-none-eabi-objdump"\n'
            'readelf = "arm-none-eabi-readelf"\n'
            'nm = "arm-none-eabi-nm"'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.compiler_path == "/opt/gcc/bin"
        assert cfg.objdump == "arm-none-eabi-objdump"
        assert cfg.readelf == "arm-none-eabi-readelf"
        assert cfg.nm == "arm-none-eabi-nm"

    def test_no_build_config_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.build_command == ""
        assert cfg.clean_command == ""
        assert cfg.objdump == ""
