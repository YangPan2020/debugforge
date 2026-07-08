"""BenchMark Counter (BMC) performance analysis tools for TriCore.

Provides access to on-chip hardware performance counters for profiling
cache hits/misses, instruction counts, branch predictions, and other
architectural events.

Reference: debugger_tricore.pdf "CPU specific BMC Commands" section.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def bmc_configure(counter: str, event: str) -> str:
    """Configure a BenchMark Counter to count a specific hardware event.

    Maps a performance event to a counter slot. The counter accumulates
    while the target runs. Read with bmc_read() after halting.

    Args:
        counter: Counter slot — "M1CNT", "M2CNT", "M3CNT", "M4CNT", etc.
        event: Hardware event to count. Common TriCore events:
               "CYCLECOUNT" — CPU clock cycles
               "INSTRUCTIONCOUNT" — instructions executed
               "DATA_X_HIT" — data cache/buffer hits
               "DATA_X_CLEAN" — data cache/buffer misses
               "DATA_READ" — data read accesses
               "DATA_WRITE" — data write accesses
               "PROGRAM_X_HIT" — instruction cache hits
               "PROGRAM_X_MISS" — instruction cache misses
               "JUMP" — jump/branch instructions
               "BRANCH_PREDICTED" — correctly predicted branches
               "BRANCH_NOT_PREDICTED" — mispredicted branches

    Returns:
        Confirmation of counter configuration
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"BMC.{counter}.EVENT {event}")
        return f"BMC configured: {counter} → counting {event}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring BMC {counter}: {e}"


@mcp.tool()
async def bmc_read(counters: list[str] | None = None) -> str:
    """Read current BenchMark Counter values.

    Target must be halted. Returns raw counter values since last reset.

    Args:
        counters: List of counter names to read (e.g., ["M1CNT", "M2CNT"]).
                  If empty/None, reads all available counters.

    Returns:
        Counter names and their current values
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "BMC.state")
        if not result.strip():
            return "BMC state not available (counters may not be configured)"
        return f"BMC State:\n{result}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading BMC: {e}"


@mcp.tool()
async def bmc_reset() -> str:
    """Reset all BenchMark Counters to zero.

    Clears all counter values for a fresh measurement.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        # Reset each common counter
        for cnt in ["M1CNT", "M2CNT", "M3CNT", "M4CNT"]:
            try:
                dbg.cmd(f"BMC.{cnt}.EVENT OFF")
            except Exception:
                pass
        # Re-open state to clear
        dbg.cmd("BMC.state")
        return "All BMC counters reset"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error resetting BMC: {e}"


@mcp.tool()
async def bmc_cache_analysis(
    function: str = "",
    run_duration_ms: int = 1000,
) -> str:
    """Run a quick cache performance analysis.

    Configures counters for cache hit/miss ratio, runs the target briefly,
    then reports the results. Useful for identifying cache bottlenecks.

    Args:
        function: Function to analyze (empty = current execution point)
        run_duration_ms: How long to run in milliseconds (default: 1000)

    Returns:
        Cache hit/miss statistics
    """
    dbg = state.require_connection()
    try:
        results = ["Cache Performance Analysis:"]

        # Configure counters for cache analysis
        dbg.cmd("BMC.M1CNT.EVENT DATA_X_HIT")
        results.append("  M1CNT: Data cache hits")
        dbg.cmd("BMC.M2CNT.EVENT DATA_X_CLEAN")
        results.append("  M2CNT: Data cache misses")
        dbg.cmd("BMC.M3CNT.EVENT PROGRAM_X_HIT")
        results.append("  M3CNT: Instruction cache hits")
        dbg.cmd("BMC.M4CNT.EVENT PROGRAM_X_MISS")
        results.append("  M4CNT: Instruction cache misses")

        # Set a breakpoint if function specified
        if function:
            dbg.cmd(f"Break.Set {function} /Program")
            dbg.cmd("Go")
            results.append(f"  Running to {function}...")
        else:
            dbg.cmd("Go")
            results.append("  Running...")

        # Wait for the specified duration
        import asyncio
        await asyncio.sleep(run_duration_ms / 1000.0)

        # Halt and read
        dbg.cmd("Break")
        results.append("  Halted. Reading counters...")

        # Read BMC state
        bmc_result = _read_window(dbg, "BMC.state")
        if bmc_result.strip():
            results.append(f"\n{bmc_result}")

        return "\n".join(results)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error in cache analysis: {e}"


@mcp.tool()
async def bmc_set_atob(counter: str, enabled: bool = True) -> str:
    """Enable or disable A-to-B mode on a BMC counter.

    In A-to-B mode, the counter only counts events between the Alpha
    and Bravo marker breakpoints. Use set_breakpoint with actions
    "alpha"/"bravo" to set markers.

    Args:
        counter: Counter name (e.g., "M1CNT")
        enabled: True to enable A-to-B mode, False to disable

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        state_str = "ON" if enabled else "OFF"
        dbg.cmd(f"BMC.{counter}.ATOB {state_str}")
        return f"BMC {counter} A-to-B mode: {state_str}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting A-to-B mode: {e}"


@mcp.tool()
async def bmc_profile_chart(counters: list[str] | None = None) -> str:
    """Display a BMC profile chart with counter data mapped to instruction flow.

    Shows which functions/addresses consumed the most events (cycles,
    cache misses, etc.). Requires BMC counters to have been recorded
    during execution.

    Args:
        counters: Counter names to include (e.g., ["M1CNT", "M2CNT"]).
                  Empty = all configured counters.

    Returns:
        Profile chart showing event distribution across code
    """
    dbg = state.require_connection()
    try:
        if counters:
            cnt_str = " ".join(counters)
            cmd = f"SNOOPer.PROfileChart.COUNTER %Up {cnt_str}"
        else:
            cmd = "SNOOPer.PROfileChart.COUNTER %Up M1CNT M2CNT M3CNT"

        result = _read_window(dbg, cmd)
        if not result.strip():
            return "No profile data available (record BMC data first using bmc_cache_analysis)"
        return result
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting BMC profile chart: {e}"
