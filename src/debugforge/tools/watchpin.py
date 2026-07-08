"""WatchPin hardware trigger output tools for TriCore AURIX.

Provides control over hardware WatchPin outputs that can generate logic analyzer
triggers or oscilloscope signals when the target halts or hits specific conditions.

Reference: debugger_tricore.pdf "CPU specific WatchPin Commands" section.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state
from debugforge.tools.views import _read_window


@mcp.tool()
async def watchpin_enable() -> str:
    """Enable WatchPin output hardware.

    Activates the WatchPin output pins on the debugger. These pins generate
    logic signals that can be connected to external test equipment.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("WatchPin.Enable")
        return "WatchPin outputs enabled"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error enabling WatchPin: {e}"


@mcp.tool()
async def watchpin_disable() -> str:
    """Disable WatchPin output hardware.

    Deactivates all WatchPin outputs.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd("WatchPin.Disable")
        return "WatchPin outputs disabled"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error disabling WatchPin: {e}"


@mcp.tool()
async def watchpin_configure(
    pin: int,
    trigger: str = "break",
    polarity: str = "high",
) -> str:
    """Configure a WatchPin to trigger on specific events.

    Args:
        pin: WatchPin number (1, 2, 3, or 4 depending on hardware)
        trigger: Trigger condition:
                 "break" — pulse when target halts
                 "go" — pulse when target runs
                 "trace_start" — pulse when trace recording starts
                 "trace_stop" — pulse when trace recording stops
        polarity: Output polarity — "high" (active high) or "low" (active low)

    Returns:
        Confirmation of WatchPin configuration
    """
    dbg = state.require_connection()
    try:
        trigger_map = {
            "break": "Break",
            "go": "Go",
            "trace_start": "TraceStart",
            "trace_stop": "TraceStop",
        }
        pol_map = {
            "high": "High",
            "low": "Low",
        }

        trig_val = trigger_map.get(trigger)
        pol_val = pol_map.get(polarity)

        if not trig_val:
            return f"Invalid trigger '{trigger}'. Use: break, go, trace_start, trace_stop"
        if not pol_val:
            return f"Invalid polarity '{polarity}'. Use: high, low"

        dbg.cmd(f"WatchPin.Set {pin}. {trig_val} {pol_val}")
        return f"WatchPin {pin} configured: trigger={trigger}, polarity={polarity}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error configuring WatchPin {pin}: {e}"


@mcp.tool()
async def watchpin_set_action_breakpoint(
    address: str,
    pin: int,
    pulse_width_us: int = 100,
) -> str:
    """Set an action breakpoint that pulses a WatchPin when hit.

    Useful for correlating software events with external hardware (e.g., oscilloscope).
    The target briefly stops, the WatchPin pulses, then execution resumes.

    Args:
        address: Address or symbol name
        pin: WatchPin number to pulse
        pulse_width_us: Pulse width in microseconds (default: 100)

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        # Set WatchPin output via PRACTICE command
        wp_cmd = f"WatchPin.Set {pin}. High"
        dbg.cmd(f'Break.Set {address} /Program /CMD "{wp_cmd}" /RESUME')
        return f"Action breakpoint at {address} — pulses WatchPin {pin} ({pulse_width_us}us)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting WatchPin action breakpoint: {e}"


@mcp.tool()
async def watchpin_state() -> str:
    """Get current WatchPin configuration and state.

    Shows which WatchPins are enabled, their trigger conditions, and polarity.

    Returns:
        WatchPin state information
    """
    dbg = state.require_connection()
    try:
        result = _read_window(dbg, "WatchPin.state")
        if not result.strip():
            return "WatchPin state not available (hardware may not support WatchPin)"
        return f"WatchPin State:\n{result}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error getting WatchPin state: {e}"


@mcp.tool()
async def watchpin_manual_pulse(pin: int, duration_ms: int = 10) -> str:
    """Manually pulse a WatchPin for testing.

    Useful for verifying WatchPin hardware connections before setting up
    automatic triggers.

    Args:
        pin: WatchPin number
        duration_ms: Pulse duration in milliseconds (default: 10)

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"WatchPin.Set {pin}. High")
        # Wait for duration
        import asyncio
        await asyncio.sleep(duration_ms / 1000.0)
        dbg.cmd(f"WatchPin.Set {pin}. Low")
        return f"WatchPin {pin} pulsed for {duration_ms}ms"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error pulsing WatchPin {pin}: {e}"
