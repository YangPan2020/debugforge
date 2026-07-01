"""Tests for workflow orchestration tools."""

from __future__ import annotations

import pytest

from debugforge.state import config


class TestBuildProjectConfig:
    def test_build_command_from_config(self, tmp_path, monkeypatch):
        from debugforge.config import load_config
        config_file = tmp_path / "debugforge.toml"
        config_file.write_text(
            '[build]\ncommand = "echo hello"\n'
            'clean_command = "echo clean"\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.build_command == "echo hello"
        assert cfg.clean_command == "echo clean"


class TestFlashAndRunConfig:
    def test_flash_script_from_config(self, tmp_path, monkeypatch):
        from debugforge.config import load_config
        config_file = tmp_path / "debugforge.toml"
        config_file.write_text(
            '[scripts]\nflash = "tools/flash.cmm"\n'
            'init = "tools/init.cmm"\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.scripts["flash"] == str(tmp_path / "tools/flash.cmm")
        assert cfg.scripts["init"] == str(tmp_path / "tools/init.cmm")

    def test_no_scripts_returns_empty(self, tmp_path, monkeypatch):
        from debugforge.config import load_config
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEBUGFORGE_CONFIG", raising=False)
        cfg = load_config()
        assert cfg.scripts == {}


class TestBuildProjectExecution:
    @pytest.mark.asyncio
    async def test_build_no_command_returns_error(self, monkeypatch):
        from debugforge.tools.build import build_project
        monkeypatch.setattr(config, "build_command", "")
        result = await build_project()
        assert "No build command configured" in result

    @pytest.mark.asyncio
    async def test_build_success(self, monkeypatch):
        from debugforge.tools.build import build_project
        monkeypatch.setattr(config, "build_command", "echo build_ok")
        monkeypatch.setattr(config, "build_working_dir", "")
        monkeypatch.setattr(config, "_base_dir", "")
        result = await build_project()
        assert "successful" in result.lower()
        assert "build_ok" in result

    @pytest.mark.asyncio
    async def test_build_failure(self, monkeypatch):
        from debugforge.tools.build import build_project
        monkeypatch.setattr(config, "build_command", "exit 1")
        monkeypatch.setattr(config, "build_working_dir", "")
        monkeypatch.setattr(config, "_base_dir", "")
        result = await build_project()
        assert "FAILED" in result

    @pytest.mark.asyncio
    async def test_clean_no_command_returns_error(self, monkeypatch):
        from debugforge.tools.build import clean_project
        monkeypatch.setattr(config, "clean_command", "")
        result = await clean_project()
        assert "No clean command configured" in result

    @pytest.mark.asyncio
    async def test_clean_success(self, monkeypatch):
        from debugforge.tools.build import clean_project
        monkeypatch.setattr(config, "clean_command", "echo cleaned")
        monkeypatch.setattr(config, "build_working_dir", "")
        monkeypatch.setattr(config, "_base_dir", "")
        result = await clean_project()
        assert "successful" in result.lower()


class TestDisassemble:
    @pytest.mark.asyncio
    async def test_no_elf_returns_error(self, monkeypatch):
        from debugforge.tools.build import disassemble
        monkeypatch.setattr(config, "elf", "")
        result = await disassemble(symbol="main")
        assert "No ELF file configured" in result

    @pytest.mark.asyncio
    async def test_no_objdump_returns_error(self, monkeypatch):
        from debugforge.tools.build import disassemble
        monkeypatch.setattr(config, "elf", "/tmp/test.elf")
        monkeypatch.setattr(config, "objdump", "")
        result = await disassemble(symbol="main")
        assert "No objdump tool configured" in result

    @pytest.mark.asyncio
    async def test_no_symbol_or_address_returns_error(self, monkeypatch):
        from debugforge.tools.build import disassemble
        monkeypatch.setattr(config, "elf", "/tmp/test.elf")
        monkeypatch.setattr(config, "objdump", "objdump")
        monkeypatch.setattr(config, "compiler_path", "")
        result = await disassemble()
        assert "Provide either" in result


class TestAnalyzeMap:
    @pytest.mark.asyncio
    async def test_no_map_returns_error(self, monkeypatch):
        from debugforge.tools.build import analyze_map
        monkeypatch.setattr(config, "map", "")
        result = await analyze_map()
        assert "No MAP file configured" in result

    @pytest.mark.asyncio
    async def test_map_not_found(self, monkeypatch):
        from debugforge.tools.build import analyze_map
        monkeypatch.setattr(config, "map", "/nonexistent/file.map")
        result = await analyze_map()
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_map_overview(self, tmp_path, monkeypatch):
        from debugforge.tools.build import analyze_map
        map_file = tmp_path / "test.map"
        map_file.write_text(".text 0x00000000 0x1000 main.o\n.bss 0x20000000 0x100 main.o\n")
        monkeypatch.setattr(config, "map", str(map_file))
        result = await analyze_map()
        assert ".text" in result
        assert ".bss" in result

    @pytest.mark.asyncio
    async def test_map_symbol_search(self, tmp_path, monkeypatch):
        from debugforge.tools.build import analyze_map
        map_file = tmp_path / "test.map"
        map_file.write_text(
            ".text 0x00000000 main\n"
            ".text 0x00000100 my_function\n"
            ".bss 0x20000000 global_var\n"
        )
        monkeypatch.setattr(config, "map", str(map_file))
        result = await analyze_map(symbol="my_function")
        assert "my_function" in result


class TestAnalyzeElf:
    @pytest.mark.asyncio
    async def test_no_elf_returns_error(self, monkeypatch):
        from debugforge.tools.build import analyze_elf
        monkeypatch.setattr(config, "elf", "")
        result = await analyze_elf()
        assert "No ELF file configured" in result

    @pytest.mark.asyncio
    async def test_no_readelf_returns_error(self, monkeypatch):
        from debugforge.tools.build import analyze_elf
        monkeypatch.setattr(config, "elf", "/tmp/test.elf")
        monkeypatch.setattr(config, "readelf", "")
        result = await analyze_elf()
        assert "No readelf tool configured" in result
