"""System configuration tools for TriCore AURIX debugging.

Covers reset behavior, cache read options, peripheral suspend, watchdog
handling, system options, and startup script execution.

Reference: debugger_tricore.pdf "System Options", "Reset Behavior",
"Accessing Cached Memory", "Suspending Peripherals" sections.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def set_reset_behavior(behavior: str) -> str:
    """Configure reset behavior for the debugger.

    Determines how TRACE32 handles soft resets, hard resets, and power cycles.

    Args:
        behavior: Reset behavior mode:
                  "restore_go" — halt briefly to restore debug resources, then continue
                  "run_restore" — restore debug resources while CPU runs (may miss breakpoints)
                  "halt" — halt CPU at reset vector after reset

    Returns:
        Confirmation of reset behavior setting
    """
    dbg = state.require_connection()
    try:
        behavior_map = {
            "restore_go": "RestoreGo",
            "run_restore": "RunRestore",
            "halt": "Halt",
        }
        val = behavior_map.get(behavior)
        if not val:
            return f"Invalid behavior '{behavior}'. Use: restore_go, run_restore, halt"

        dbg.cmd(f"SYStem.Option.RESetBehavior {val}")
        return f"Reset behavior set to: {val}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting reset behavior: {e}"


@mcp.tool()
async def set_cache_read(enabled: bool = True) -> str:
    """Enable or disable cache-aware memory reads.

    When ON, the default data access class (D:) shows cached data from the
    CPU's point of view instead of stale bus-level data.
    Essential for debugging code that modifies cached memory (e.g., LMU on TC39x).

    Args:
        enabled: True to enable cache-aware reads, False to disable

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        state_str = "ON" if enabled else "OFF"
        dbg.cmd(f"SYStem.Option.DCREAD {state_str}")
        return f"Cache-aware reads (DCREAD): {state_str}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting DCREAD: {e}"


@mcp.tool()
async def set_peripheral_suspend(enabled: bool = True) -> str:
    """Enable or disable automatic peripheral suspend when CPU halts.

    When ON, peripheral modules (timers, watchdogs, communication) are
    automatically suspended when the debugger halts the CPU. This prevents
    watchdog timeouts and timer overflows during debugging.

    Args:
        enabled: True to enable peripheral suspend, False to disable

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        state_str = "ON" if enabled else "OFF"
        dbg.cmd(f"SYStem.Option.PERSTOP {state_str}")
        return f"Peripheral suspend (PERSTOP): {state_str}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting PERSTOP: {e}"


@mcp.tool()
async def suspend_peripheral(peripheral: str, suspend_mode: str = "hard") -> str:
    """Configure suspend mode for a specific peripheral module.

    Sets how a peripheral responds when the CPU is halted by the debugger.

    Args:
        peripheral: Peripheral register name (e.g., "GPT120_OCS", "STM0_OCS")
        suspend_mode: "hard" — suspend immediately on CPU halt
                      "soft" — suspend after current operation completes
                      "none" — never suspend

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        mode_map = {
            "hard": "Set hard suspend",
            "soft": "Set soft suspend",
            "none": "No suspend",
        }
        mode_val = mode_map.get(suspend_mode)
        if not mode_val:
            return f"Invalid suspend mode '{suspend_mode}'. Use: hard, soft, none"

        dbg.cmd(f'PER.Set.ByName .{peripheral}.SUS "{mode_val}"')
        return f"Peripheral '{peripheral}' suspend: {suspend_mode}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring peripheral suspend: {e}"


@mcp.tool()
async def set_standby_mode(enabled: bool = True) -> str:
    """Enable or disable standby mode for power cycle detection.

    When ON, TRACE32 monitors VTREF to detect power cycles and can
    automatically reconnect and restore debug state.

    Args:
        enabled: True to enable standby mode, False to disable

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        mode = "StandBy" if enabled else "NoStandBy"
        dbg.cmd(f"SYStem.Mode {mode}")
        return f"Standby mode: {mode}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting standby mode: {e}"


@mcp.tool()
async def get_system_options() -> str:
    """Get the current system options and configuration.

    Shows all active SYStem.Option settings including PERSTOP, DCREAD,
    reset behavior, and other debug options.

    Returns:
        Formatted system options
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "SYStem.Option")
        if not result.strip():
            # Fallback: query known options individually
            parts = ["System Options:"]
            try:
                dbg.cmd("SYStem.CONFIG.state")
                config_result = _read_window(dbg, "SYStem.CONFIG.state")
                if config_result.strip():
                    parts.append(config_result)
            except Exception:
                pass
            return "\n".join(parts)
        return f"System Options:\n{result}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting system options: {e}"


@mcp.tool()
async def load_symbol_file(elf_path: str = "") -> str:
    """Load debug symbols from an ELF file.

    Loads symbol and debug information for source-level debugging.
    If no path given, uses the configured ELF path from debugforge.toml.

    Args:
        elf_path: Path to ELF file. Empty = use configured path.

    Returns:
        Confirmation of symbol loading
    """
    from debugforge.state import config as cfg

    dbg = state.require_connection()
    path = elf_path or cfg.elf
    if not path:
        return "Error: No ELF path specified and no [project] elf configured in debugforge.toml"

    try:
        dbg.cmd(f'Data.LOAD.Elf "{path}"')
        return f"Symbols loaded from: {path}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error loading symbols from {path}: {e}"


@mcp.tool()
async def run_cmm_script(script_path: str, timeout: float = 30.0) -> str:
    """Execute a TRACE32 PRACTICE (.cmm) script file.

    Args:
        script_path: Path to the .cmm script file
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Script execution result
    """
    dbg = state.require_connection()
    try:
        dbg.cmm(f'DO "{script_path}"', timeout=timeout)
        return f"Script executed: {script_path}"
    except ConnectionError:
        raise
    except TimeoutError:
        return f"Script timed out after {timeout}s: {script_path}"
    except Exception as e:
        return f"Error running script {script_path}: {e}"


@mcp.tool()
async def set_system_option(option: str, value: str) -> str:
    """Set a specific SYStem.Option value.

    Generic tool for any SYStem.Option.* setting not covered by dedicated tools.

    Args:
        option: Option name (e.g., "PERSTOP", "DCREAD", "RESYNC")
        value: Value to set (e.g., "ON", "OFF", "RestoreGo")

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"SYStem.Option.{option} {value}")
        return f"SYStem.Option.{option} = {value}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting option {option}: {e}"
