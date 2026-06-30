"""Execution control tools for TRACE32."""

from __future__ import annotations

from mcp_trace32.server import mcp
from mcp_trace32.state import state


@mcp.tool()
async def go() -> str:
    """Start or continue program execution on the target.

    Returns:
        Confirmation that execution was started
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Go")
        return "Program execution started"
    except Exception as e:
        return f"Error starting execution: {e}"


@mcp.tool()
async def step(mode: str = "into") -> str:
    """Single-step program execution.

    Args:
        mode: Step mode — "into" (step into functions), "over" (step over),
              "out" (step out of current function)

    Returns:
        New program counter address after step
    """
    dbg = state.require_connection()
    cmd_map = {
        "into": "Step",
        "over": "Step.Over",
        "out": "Step.Out",
    }
    cmd = cmd_map.get(mode)
    if cmd is None:
        return f"Invalid step mode '{mode}'. Use: into, over, out"

    try:
        dbg.cmd(cmd)
        try:
            pc = dbg.fnc.register_pc()
            return f"Stepped ({mode}). PC = 0x{pc:08X}"
        except Exception:
            return f"Stepped ({mode}). Use 'read_register' to check PC."
    except Exception as e:
        return f"Error during step: {e}"


@mcp.tool()
async def halt() -> str:
    """Stop (break) program execution on the target.

    Returns:
        CPU state after halting
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Break")
        try:
            pc = dbg.fnc.register_pc()
            return f"Execution halted. PC = 0x{pc:08X}"
        except Exception:
            return "Execution halted"
    except Exception as e:
        return f"Error halting execution: {e}"


@mcp.tool()
async def reset() -> str:
    """Reset the target CPU.

    Returns:
        Confirmation of reset
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("SYStem.RESetTarget")
        return "Target reset complete"
    except Exception as e:
        return f"Error resetting target: {e}"


@mcp.tool()
async def get_state() -> str:
    """Get the current CPU/target execution state.

    Returns:
        Current state: running, stopped, power-down, or other system state
    """
    dbg = state.require_connection()
    try:
        sys_mode = dbg.fnc.system_mode()
        info = f"System mode: {sys_mode}"
        try:
            run_state = dbg.fnc.state_run()
            if run_state:
                info += "\nCPU: Running"
            else:
                pc = dbg.fnc.register_pc()
                info += f"\nCPU: Stopped at PC = 0x{pc:08X}"
        except Exception:
            pass
        return info
    except Exception as e:
        return f"Error getting state: {e}"
