"""Event notification and message line tools for TRACE32.

Provides tools for TRACE32 message line (MSG), event notifications, and
communication between PRACTICE scripts and the debugger.

Reference: debugger_tricore.pdf "Event Notifications", "MSG command" sections.
"""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state


@mcp.tool()
async def send_message(text: str, level: str = "info") -> str:
    """Display a message in the TRACE32 message line (MSG).

    Messages appear in the TRACE32 GUI status bar and can be used for
    debugging status, progress updates, or user notifications.

    Args:
        text: Message text to display
        level: Message level — "info", "warning", "error"

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        level_map = {
            "info": "PRINT",
            "warning": "PRINT %WARNING",
            "error": "PRINT %ERROR",
        }
        cmd = level_map.get(level, "PRINT")
        dbg.cmd(f'{cmd} "{text}"')
        return f"Message displayed: [{level}] {text}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error sending message: {e}"


@mcp.tool()
async def clear_message() -> str:
    """Clear the TRACE32 message line.

    Removes any displayed message from the status bar.

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd('PRINT ""')
        return "Message line cleared"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error clearing message: {e}"


@mcp.tool()
async def enable_event_notifications(events: list[str] | None = None) -> str:
    """Enable event notifications for debugger state changes.

    When enabled, TRACE32 can send notifications to external tools or scripts
    when specific events occur (e.g., target halts, breakpoints hit).

    Args:
        events: List of event types to monitor:
                "break" — target halted
                "go" — target running
                "reset" — system reset detected
                "power" — power cycle detected
                Default: ["break", "go"]

    Returns:
        Confirmation of enabled events
    """
    dbg = state.require_connection()
    try:
        evt_list = events or ["break", "go"]
        results = []

        for evt in evt_list:
            evt_map = {
                "break": "ENDBREAK",
                "go": "ENDGO",
                "reset": "ENDRESET",
                "power": "ENDPOWER",
            }
            evt_code = evt_map.get(evt)
            if evt_code:
                dbg.cmd(f"EVENT.ON {evt_code}")
                results.append(f"  Enabled: {evt}")
            else:
                results.append(f"  Warning: unknown event '{evt}' (skipped)")

        return f"Event notifications configured:\n" + "\n".join(results)
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error enabling event notifications: {e}"


@mcp.tool()
async def set_event_action(event: str, command: str) -> str:
    """Set a command to execute when a specific event occurs.

    Allows automated responses to debugger events (e.g., run a script
    when target halts, collect trace data on breakpoint hit).

    Args:
        event: Event type — "break", "go", "reset", "power"
        command: TRACE32 command to execute (e.g., "DO my_script.cmm",
                 "Var.view myVar", "Trace.List")

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        evt_map = {
            "break": "ENDBREAK",
            "go": "ENDGO",
            "reset": "ENDRESET",
            "power": "ENDPOWER",
        }
        evt_code = evt_map.get(event)
        if not evt_code:
            return f"Invalid event '{event}'. Use: break, go, reset, power"

        escaped_cmd = command.replace('"', '""')
        dbg.cmd(f'EVENT.{evt_code} "{escaped_cmd}"')
        return f"Event action set: {event} → {command}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting event action: {e}"


@mcp.tool()
async def set_debugger_mode(mode: str) -> str:
    """Set the debugger operational mode.

    Controls how TRACE32 responds to target state changes.

    Args:
        mode: Debugger mode:
              "attach" — attach to running target without resetting
              "standby" — monitor power cycles, auto-reconnect
              "no_standby" — disable power cycle monitoring

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        mode_map = {
            "attach": "SYStem.Mode.Attach",
            "standby": "SYStem.Mode.StandBy",
            "no_standby": "SYStem.Mode.NoStandBy",
        }
        cmd = mode_map.get(mode)
        if not cmd:
            return f"Invalid mode '{mode}'. Use: attach, standby, no_standby"

        dbg.cmd(cmd)
        return f"Debugger mode set to: {mode}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting debugger mode: {e}"
