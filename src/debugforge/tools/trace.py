"""On-chip Trace (MCDS) control tools for TRACE32 — TriCore AURIX.

Implements on-chip trace recording: program trace, data trace (read/write),
timestamped trace, and trace-trigger breakpoints. Based on MCDS (Multi-core
Debug Support) hardware on AURIX devices.

Reference: debugger_tricore.pdf "On-chip Trace" section.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def trace_start(
    sources: list[str] | None = None,
    timestamps: bool = True,
) -> str:
    """Start on-chip trace recording using MCDS.

    Configures and starts the MCDS trace engine. Must be called before running
    the target. Call trace_stop() and trace_list() after the target halts.

    Args:
        sources: List of trace sources to enable. Supported values:
                 "program" — instruction flow (PC trace)
                 "write_addr" — data write addresses
                 "write_data" — data write values
                 "read_addr" — data read addresses
                 "read_data" — data read values
                 Default: ["program"]
        timestamps: Enable trace timestamps (default: True)

    Returns:
        Confirmation of trace configuration
    """
    dbg = state.require_connection()
    try:
        results = []

        # Open MCDS state window
        dbg.cmd("MCDS.state")
        results.append("MCDS state window opened")

        # Enable MCDS clock
        dbg.cmd("CLOCK.ON")
        results.append("MCDS clock enabled")

        # Enable timestamps
        if timestamps:
            dbg.cmd("MCDS.TimeStamp.ON")
            results.append("Timestamps enabled")

        # Configure trace sources
        src_list = sources or ["program"]
        source_map = {
            "program": "TriCore.Program",
            "write_addr": "TriCore.WriteAddr",
            "write_data": "TriCore.WriteData",
            "read_addr": "TriCore.ReadAddr",
            "read_data": "TriCore.ReadData",
        }

        for src in src_list:
            mcds_src = source_map.get(src)
            if mcds_src:
                dbg.cmd(f"MCDS.SOURCE.Set {mcds_src} ON")
                results.append(f"Source enabled: {mcds_src}")
            else:
                results.append(f"Warning: unknown source '{src}' (skipped)")

        return f"Trace configured:\n" + "\n".join(f"  {r}" for r in results)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error starting trace: {e}"


@mcp.tool()
async def trace_stop() -> str:
    """Stop the on-chip trace recording.

    Call after the target halts (e.g., at a breakpoint or after manual halt).

    Returns:
        Confirmation that trace recording stopped
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Trace.Off")
        return "Trace recording stopped"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error stopping trace: {e}"


@mcp.tool()
async def trace_list(max_records: int = 100) -> str:
    """Display the recorded trace buffer contents.

    Shows the trace list with instruction flow, data accesses, and timestamps
    (if enabled). The target must be halted.

    Args:
        max_records: Maximum number of trace records to display (default: 100)

    Returns:
        Formatted trace listing
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "Trace.List", max_size=max_records * 200)
        if not result.strip():
            return "Trace buffer empty (no trace data recorded, or trace not started)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading trace: {e}"


@mcp.tool()
async def trace_clear() -> str:
    """Clear the trace buffer.

    Resets the MCDS trace buffer for a fresh recording.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("Trace.RESet")
        return "Trace buffer cleared"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error clearing trace: {e}"


@mcp.tool()
async def trace_set_trigger(
    address: str,
    trigger_type: str = "stop",
) -> str:
    """Set a trace trigger breakpoint.

    Configures a breakpoint that controls trace recording start/stop.

    Args:
        address: Function name, symbol, or address (e.g., "sieve", "0x80001000").
                 Supports symbol.EXIT(func) syntax for function exit triggers.
        trigger_type: "stop" — stop recording at this point (TraceTrigger)
                      "enable" — enable recording at this point (TraceEnable)
                      "disable" — disable recording at this point

    Returns:
        Confirmation of trace trigger
    """
    dbg = state.require_connection()
    try:
        type_map = {
            "stop": "/TraceTrigger",
            "enable": "/TraceEnable",
            "disable": "/TraceDisable",
        }
        flag = type_map.get(trigger_type)
        if not flag:
            return f"Invalid trigger type '{trigger_type}'. Use: stop, enable, disable"

        dbg.cmd(f"Break.Set {address} /Program {flag}")
        return f"Trace trigger set: {trigger_type} @ {address}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting trace trigger: {e}"


@mcp.tool()
async def trace_data_write(
    variable: str,
    data_value: str = "",
    data_width: str = "auto",
) -> str:
    """Configure data write trace on a variable.

    Records every write access to the specified variable in the trace buffer.
    Optionally filters by data value.

    Args:
        variable: Variable name or address (e.g., "flags[12]", "myVar", "0xD0000100")
        data_value: Optional filter — only trace writes matching this value (e.g., "0x33")
        data_width: Data width for value matching — "byte", "word", "long", "quad", "auto"

    Returns:
        Confirmation of data write trace setup
    """
    dbg = state.require_connection()
    try:
        cmd = f"Var.Break.Set {variable} /Write /Onchip /TraceEnable"
        if data_value:
            width_map = {"byte": "Byte", "word": "Word", "long": "Long",
                         "quad": "Quad", "auto": "auto"}
            w = width_map.get(data_width, "auto")
            cmd += f" /Data.{w} {data_value}"

        dbg.cmd(cmd)

        # Enable data trace sources
        dbg.cmd("MCDS.SOURCE.Set TriCore.WriteAddr ON")
        dbg.cmd("MCDS.SOURCE.Set TriCore.WriteData ON")

        msg = f"Data write trace enabled on '{variable}'"
        if data_value:
            msg += f" (filter: value={data_value}, width={data_width})"
        return msg
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring data write trace: {e}"


@mcp.tool()
async def trace_data_read(
    variable: str,
) -> str:
    """Configure data read trace on a variable.

    Records every read access to the specified variable in the trace buffer.

    Args:
        variable: Variable name or address (e.g., "myVar", "0xD0000100")

    Returns:
        Confirmation of data read trace setup
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"Var.Break.Set {variable} /Read /Onchip /TraceEnable")
        dbg.cmd("MCDS.SOURCE.Set TriCore.ReadAddr ON")
        dbg.cmd("MCDS.SOURCE.Set TriCore.ReadData ON")
        return f"Data read trace enabled on '{variable}'"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring data read trace: {e}"


@mcp.tool()
async def trace_profile_chart() -> str:
    """Display a profile chart from recorded trace data.

    Shows instruction execution statistics per function based on trace data.
    Requires trace data to have been recorded first.

    Returns:
        Formatted profile chart
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "Trace.PROfileChart")
        if not result.strip():
            return "No profile data available (record trace data first)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting trace profile: {e}"


@mcp.tool()
async def trace_state() -> str:
    """Get current MCDS trace state and configuration.

    Shows the MCDS state window with current trace source settings,
    buffer status, and configuration.

    Returns:
        MCDS state information
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "MCDS.state")
        if not result.strip():
            return "MCDS state not available (on-chip trace may not be supported)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting MCDS state: {e}"
