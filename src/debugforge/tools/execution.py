"""Execution control tools for TRACE32 — run, step, halt, reset, source location."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


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
    mode_norm = mode.lower().strip()
    cmd_map = {
        "into": "Step",
        "over": "Step.Over",
        "out": "Step.Out",
        "into_hll": "Step.Hll",
        "over_hll": "Step.HllOver",
        "next_line": "Step.HllOver",
        "next_source_line": "Step.HllOver",
        "next_assembly": "Step.Over",
        "source_line": "Step.Hll",
    }
    cmd = cmd_map.get(mode_norm)
    if cmd is None:
        return (
            f"Invalid step mode '{mode}'. Use: into, over, out, into_hll, "
            "over_hll (step one source line), next_line, next_assembly, source_line"
        )

    try:
        dbg.cmd(cmd)
        try:
            pc = dbg.fnc.register_pc()
            loc = _current_source_location(dbg)
            if loc:
                return f"Stepped ({mode_norm}). PC = 0x{pc:08X}\nSource: {loc}"
            return f"Stepped ({mode_norm}). PC = 0x{pc:08X}"
        except Exception:
            return f"Stepped ({mode_norm}). Use 'read_register' to check PC."
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


def _current_source_location(dbg) -> str:
    """Return current source location as 'file:line (function)' or empty."""
    try:
        result = dbg.eval('sYmbol.FUNCtion(PP())')
    except Exception:
        result = ""
    try:
        src = dbg.eval('sYmbol.SOURCE(PP())')
    except Exception:
        src = ""
    if src:
        loc = f"{src}"
        if result:
            loc += f" in {result}"
        return loc
    return result if result else ""


@mcp.tool()
async def get_source_location() -> str:
    """Get the current source file and line of the halted CPU.

    Returns the HLL source location (file:line) and enclosing function name
    for the current PC. The target must be halted and symbols must be loaded.

    Returns:
        Formatted source location (file, line, function, module)
    """
    dbg = state.require_connection()
    try:
        pc = dbg.fnc.register_pc()
        loc = _current_source_location(dbg)
        if loc:
            return f"PC = 0x{pc:08X}\n{loc}"
        return f"PC = 0x{pc:08X} (no source location available)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting source location: {e}"


@mcp.tool()
async def step_mode_list() -> str:
    """List all supported step modes and their behavior.

    Returns:
        Table of step modes with descriptions
    """
    rows = [
        ("into", "Step into function calls (assembly-level)"),
        ("over", "Step over function calls (assembly-level)"),
        ("out", "Step out of current function to caller"),
        ("into_hll", "Step into function calls (source-line)"),
        ("over_hll", "Step over one HLL source line (next source line)"),
        ("next_line", "Alias for over_hll — next source line"),
        ("next_assembly", "Alias for over — next assembly instruction"),
        ("source_line", "Alias for into_hll — one source line"),
    ]
    lines = ["Supported step modes:", ""]
    for name, desc in rows:
        lines.append(f"  {name:20s}  {desc}")
    return "\n".join(lines)


@mcp.tool()
async def get_current_function() -> str:
    """Get the name of the function the CPU is currently executing.

    Returns:
        Function name (or address if no debug symbols)
    """
    dbg = state.require_connection()
    try:
        result = dbg.eval('sYmbol.FUNCtion(PP())')
        if result:
            return f"Current function: {result}"
        pc = dbg.fnc.register_pc()
        return f"Current function: unknown (no symbol at PC = 0x{pc:08X})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting current function: {e}"


@mcp.tool()
async def run_to_line(file: str, line: int) -> str:
    """Run until execution reaches a specific source file line.

    Sets a temporary breakpoint at the given source location and resumes
    execution. The target stops when that line is reached.

    Args:
        file: Source file name (can be partial, e.g., 'main.c' or full path)
        line: Line number in the source file

    Returns:
        Confirmation of temporary breakpoint
    """
    dbg = state.require_connection()
    try:
        # TRACE32 syntax: Break.Set "file"\line /Program /Temp
        escaped_file = file.replace('"', '""')
        dbg.cmd(f'Break.Set "{escaped_file}"\\{line} /Program')
        dbg.cmd("Go")
        return f"Running to {file}:{line}..."
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting run-to-line at {file}:{line}: {e}"


@mcp.tool()
async def get_run_stats() -> str:
    """Get quick run/halt statistics for the target.

    Combines CPU state, current function, source location, and elapsed
    runtime (if available) in one call.

    Returns:
        Aggregated run statistics
    """
    dbg = state.require_connection()
    try:
        parts = ["# Run Statistics", ""]
        try:
            run_state = dbg.fnc.state_run()
            parts.append(f"Running: {run_state}")
        except Exception as e:
            parts.append(f"State check failed: {e}")

        try:
            pc = dbg.fnc.register_pc()
            parts.append(f"PC: 0x{pc:08X}")
        except Exception:
            pass

        loc = _current_source_location(dbg)
        if loc:
            parts.append(f"Location: {loc}")

        try:
            sys_mode = dbg.fnc.system_mode()
            parts.append(f"System mode: {sys_mode}")
        except Exception:
            pass

        return "\n".join(parts)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting run stats: {e}"


@mcp.tool()
async def get_practice_state() -> str:
    """Get the state of any running PRACTICE (.cmm) script.

    Shows whether a PRACTICE script is active, which script is running,
    and the current line being executed.

    Returns:
        PRACTICE script state
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "PRactice.state")
        if not result.strip():
            return "No PRACTICE script running"
        return f"PRACTICE State:\n{result}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting PRACTICE state: {e}"


@mcp.tool()
async def abort_practice() -> str:
    """Abort the currently running PRACTICE script.

    Stops the active .cmm script execution immediately.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("PRactice.ABORT")
        return "PRACTICE script aborted"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error aborting PRACTICE script: {e}"


@mcp.tool()
async def get_message_line() -> str:
    """Read the current TRACE32 message line content.

    The message line is the status bar at the bottom of the TRACE32 window
    that displays status messages from commands and scripts.

    Returns:
        Current message line text
    """
    dbg = state.require_connection()
    try:
        result = dbg.eval('MSG.line()')
        return f"Message line: '{result}'" if result else "Message line: (empty)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading message line: {e}"
