"""Project configuration for DebugForge."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class RemoteConfig:
    """Remote connection configuration (WinRM/SSH)."""

    host: str = ""
    mode: str = "local"
    winrm_port: int = 5985
    winrm_user: str = ""
    winrm_password: str = ""
    winrm_transport: str = "ntlm"
    ssh_user: str = ""
    ssh_password: str = ""
    ssh_port: int = 22
    staging_dir: str = ""
    source_translates: list[dict[str, str]] = field(default_factory=list)

    @property
    def winrm_url(self) -> str:
        if not self.host:
            return ""
        return f"http://{self.host}:{self.winrm_port}/wsman"


@dataclass
class DebugForgeConfig:
    """DebugForge project configuration."""

    # TRACE32 settings
    t32_install_path: str = ""

    # Connection settings
    node: str = "localhost"
    port: int = 20000
    protocol: str = "TCP"
    auto_connect: bool = False

    # Project paths (resolved to absolute)
    elf: str = ""
    map: str = ""

    # Scripts (resolved to absolute)
    scripts: dict[str, str | list[str]] = field(default_factory=dict)

    # Toolchain settings
    compiler_path: str = ""
    objdump: str = ""
    readelf: str = ""
    nm: str = ""

    # Build settings
    build_command: str = ""
    clean_command: str = ""
    build_working_dir: str = ""

    # Debug settings
    skills_dir: str = ""

    # Remote settings
    remote: RemoteConfig = field(default_factory=RemoteConfig)

    # Base directory for resolving relative paths
    _base_dir: str = field(default="", repr=False)

    @property
    def config_dir(self) -> str:
        return self._base_dir


def _resolve_path(path: str, base_dir: str) -> str:
    """Resolve a path relative to base_dir if not absolute."""
    if not path:
        return ""
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(Path(base_dir) / p)


def load_config(config_path: str | None = None) -> DebugForgeConfig:
    """Load configuration from TOML file and environment variables.

    Search order for config file:
      1. Explicit config_path argument
      2. $DEBUGFORGE_CONFIG environment variable
      3. debugforge.toml in current working directory
      4. No file found → use defaults only

    Environment variables always override file values.
    """
    cfg = DebugForgeConfig()

    # Determine config file path
    if config_path is None:
        config_path = os.environ.get("DEBUGFORGE_CONFIG", "")
    if not config_path:
        candidate = Path.cwd() / "debugforge.toml"
        if candidate.exists():
            config_path = str(candidate)

    # Load TOML file if found
    if config_path and Path(config_path).exists():
        if tomllib is None:
            raise ImportError(
                "Python < 3.11 requires 'tomli' package to read config files. "
                "Install with: pip install tomli"
            )
        base_dir = str(Path(config_path).resolve().parent)
        cfg._base_dir = base_dir

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # [trace32]
        t32_section = data.get("trace32", {})
        if "install_path" in t32_section:
            cfg.t32_install_path = _resolve_path(t32_section["install_path"], base_dir)

        # [connection]
        conn_section = data.get("connection", {})
        if "node" in conn_section:
            cfg.node = conn_section["node"]
        if "port" in conn_section:
            cfg.port = int(conn_section["port"])
        if "protocol" in conn_section:
            cfg.protocol = conn_section["protocol"]
        if "auto_connect" in conn_section:
            cfg.auto_connect = bool(conn_section["auto_connect"])

        # [project]
        proj_section = data.get("project", {})
        if "elf" in proj_section:
            cfg.elf = _resolve_path(proj_section["elf"], base_dir)
        if "map" in proj_section:
            cfg.map = _resolve_path(proj_section["map"], base_dir)

        # [scripts]
        scripts_section = data.get("scripts", {})
        for key, val in scripts_section.items():
            if isinstance(val, str):
                cfg.scripts[key] = _resolve_path(val, base_dir)
            elif isinstance(val, list):
                cfg.scripts[key] = [_resolve_path(v, base_dir) for v in val if isinstance(v, str)]

        # [toolchain]
        tc_section = data.get("toolchain", {})
        if "compiler_path" in tc_section:
            cfg.compiler_path = _resolve_path(tc_section["compiler_path"], base_dir)
        if "objdump" in tc_section:
            cfg.objdump = tc_section["objdump"]
        if "readelf" in tc_section:
            cfg.readelf = tc_section["readelf"]
        if "nm" in tc_section:
            cfg.nm = tc_section["nm"]

        # [build]
        build_section = data.get("build", {})
        if "command" in build_section:
            cfg.build_command = build_section["command"]
        if "clean_command" in build_section:
            cfg.clean_command = build_section["clean_command"]
        if "working_dir" in build_section:
            cfg.build_working_dir = _resolve_path(build_section["working_dir"], base_dir)

        # [debug]
        debug_section = data.get("debug", {})
        if "skills_dir" in debug_section:
            cfg.skills_dir = _resolve_path(debug_section["skills_dir"], base_dir)

        # [mode]
        mode_section = data.get("mode", {})
        if "mode" in mode_section:
            cfg.remote.mode = mode_section["mode"]

        # [remote]
        remote_section = data.get("remote", {})
        if "host" in remote_section:
            cfg.remote.host = remote_section["host"]
        if "winrm_port" in remote_section:
            cfg.remote.winrm_port = int(remote_section["winrm_port"])
        if "winrm_user" in remote_section:
            cfg.remote.winrm_user = remote_section["winrm_user"]
        if "winrm_password" in remote_section:
            cfg.remote.winrm_password = remote_section["winrm_password"]
        if "winrm_transport" in remote_section:
            cfg.remote.winrm_transport = remote_section["winrm_transport"]
        if "ssh_user" in remote_section:
            cfg.remote.ssh_user = remote_section["ssh_user"]
        if "ssh_password" in remote_section:
            cfg.remote.ssh_password = remote_section["ssh_password"]
        if "ssh_port" in remote_section:
            cfg.remote.ssh_port = int(remote_section["ssh_port"])
        if "staging_dir" in remote_section:
            cfg.remote.staging_dir = remote_section["staging_dir"]
        if "port" in remote_section:
            cfg.port = int(remote_section["port"])
            cfg.remote.host = cfg.remote.host or cfg.node
        if "source_translates" in remote_section:
            cfg.remote.source_translates = remote_section["source_translates"]

    # Environment variable overrides (highest priority)
    env_install = os.environ.get("T32_INSTALL_PATH", "")
    if env_install:
        cfg.t32_install_path = env_install

    env_node = os.environ.get("T32_NODE", "")
    if env_node:
        cfg.node = env_node

    env_port = os.environ.get("T32_PORT", "")
    if env_port:
        cfg.port = int(env_port)

    env_protocol = os.environ.get("T32_PROTOCOL", "")
    if env_protocol:
        cfg.protocol = env_protocol

    env_auto = os.environ.get("T32_AUTO_CONNECT", "")
    if env_auto:
        cfg.auto_connect = env_auto.lower() == "true"

    return cfg
