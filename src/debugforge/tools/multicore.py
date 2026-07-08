"""Multicore debugging tools for TriCore AURIX — SMP, AMP, iAMP.

Covers core selection, multicore configuration, cross-core synchronization,
and chip stepping detection.

Reference: debugger_tricore.pdf "Multicore Debugging" section.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def select_core(core: int) -> str:
    """Select the active CPU core for debugging.

    In multicore setups, switches the debugger focus to the specified core.
    Subsequent commands (breakpoints, register reads, etc.) target this core.

    Args:
        core: Core number (0-based, e.g., 0, 1, 2 for TC397)

    Returns:
        Confirmation with current core state
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"SYStem.CPU {core}.")
        # Query current state
        run_state = dbg.fnc.state_run()
        if run_state:
            return f"Core {core} selected — Running"
        else:
            try:
                pc = dbg.fnc.register_pc()
                return f"Core {core} selected — Stopped at PC = 0x{pc:08X}"
            except Exception:
                return f"Core {core} selected — Stopped"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error selecting core {core}: {e}"


@mcp.tool()
async def get_chip_info() -> str:
    """Get the detected chip/device information.

    Returns chip stepping, device variant, and CPU configuration.
    Useful for verifying the correct CPU is selected.

    Returns:
        Chip stepping, CPU type, and stepping information
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "SYStem.CPU")
        info_parts = ["Chip Information:"]

        # Try to get chip stepping via PRACTICE function
        try:
            stepping = dbg.eval('CHIP.STEPping()')
            info_parts.append(f"  Chip Stepping: {stepping}")
        except Exception:
            pass

        # Get system mode
        try:
            sys_mode = dbg.fnc.system_mode()
            info_parts.append(f"  System Mode: {sys_mode}")
        except Exception:
            pass

        if result.strip():
            info_parts.append(f"\n  CPU Configuration:\n{result}")

        return "\n".join(info_parts)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting chip info: {e}"


@mcp.tool()
async def configure_multicore(core_count: int) -> str:
    """Configure multicore topology for AURIX devices.

    Mounts multiple cores into one chip for shared resources (trace, MCDS).
    Must be called before SYStem.Up in multicore scenarios.

    Based on SYStem.CONFIG.CORE command from debugger_tricore.pdf:
      SYStem.CONFIG.CORE maps each core to a chip position.

    Args:
        core_count: Number of cores to configure (e.g., 6 for TC397, 3 for TC377)

    Returns:
        Configuration results per core
    """
    dbg = state.require_connection()
    try:
        results = []
        for i in range(core_count):
            core_id = i + 1  # SYStem.CONFIG.CORE uses 1-based numbering
            chip_pos = 1  # All cores in same chip
            dbg.cmd(f"SYStem.CONFIG.CORE {core_id}. {chip_pos}.")
            results.append(f"  Core {i} → Chip position {chip_pos}, core slot {core_id}")

        return f"Multicore configured ({core_count} cores):\n" + "\n".join(results)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring multicore: {e}"


@mcp.tool()
async def sync_cores(action: str = "go") -> str:
    """Synchronize Go/Step/Break across multiple cores.

    Uses the SYnch command to coordinate execution state between cores
    in SMP or synchronized AMP mode.

    Args:
        action: Synchronization action:
                "go" — run all synchronized cores
                "break" — halt all synchronized cores
                "step" — single-step all synchronized cores

    Returns:
        Confirmation of sync operation
    """
    dbg = state.require_connection()
    try:
        cmd_map = {
            "go": "SYnch.Go",
            "break": "SYnch.Break",
            "step": "SYnch.Step",
        }
        cmd = cmd_map.get(action)
        if not cmd:
            return f"Invalid sync action '{action}'. Use: go, break, step"

        dbg.cmd(cmd)
        return f"Synchronized {action} across all cores"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error syncing cores ({action}): {e}"


@mcp.tool()
async def get_all_cores_state() -> str:
    """Get the execution state of all CPU cores.

    Queries each core's running/stopped status and PC value.
    Useful in multicore debugging to understand the global system state.

    Returns:
        Table showing state of each core
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "SYStem.CONFIG.state")
        if result.strip():
            return f"System Configuration:\n{result}"

        # Fallback: try to get state of current core
        run_state = dbg.fnc.state_run()
        if run_state:
            return "Current core: Running"
        else:
            try:
                pc = dbg.fnc.register_pc()
                return f"Current core: Stopped at PC = 0x{pc:08X}"
            except Exception:
                return "Current core: Stopped"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting core states: {e}"


@mcp.tool()
async def detect_cpu() -> str:
    """Auto-detect the connected AURIX device.

    Uses SYStem.DETECT.CPU to identify the connected chip automatically.
    Works with TC27x, TC37x, TC39x and other AURIX families.

    Returns:
        Detected CPU type and stepping
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("SYStem.DETECT.CPU")
        # Try to read chip stepping
        try:
            stepping = dbg.eval('CHIP.STEPping()')
            return f"Auto-detected CPU: {stepping}"
        except Exception:
            return "CPU auto-detection executed (use get_chip_info for details)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error detecting CPU: {e}"
