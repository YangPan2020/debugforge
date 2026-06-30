"""Command execution and scripting tools for TRACE32."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state


@mcp.tool()
async def execute_command(command: str) -> str:
    """Execute any TRACE32 PRACTICE command string.

    This is the most flexible tool — any command you can type in the TRACE32
    command line can be executed here (e.g., "SYStem.Up", "Data.LOAD.Elf ...",
    "Break.Set main", "Var.View myVar").

    Args:
        command: TRACE32 command string to execute

    Returns:
        Success confirmation or error message from TRACE32
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(command)
        return f"Command executed: {command}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Command failed '{command}': {e}"


@mcp.tool()
async def run_practice(script: str, timeout: float = 60.0) -> str:
    """Run a PRACTICE (.cmm) script and wait for it to complete.

    Args:
        script: Path to the .cmm script file (absolute or relative to TRACE32)
        timeout: Maximum time to wait for script completion in seconds (default: 60)

    Returns:
        Script execution result (success or error message)
    """
    dbg = state.require_connection()
    try:
        dbg.cmm(script, timeout=timeout)
        return f"PRACTICE script completed: {script}"
    except TimeoutError:
        return f"PRACTICE script timed out after {timeout}s: {script}"
    except ConnectionError:
        raise
    except Exception as e:
        return f"PRACTICE script error '{script}': {e}"


@mcp.tool()
async def evaluate(expression: str) -> str:
    """Evaluate a TRACE32 PRACTICE function or expression.

    Useful for querying system state, hardware info, or computing values.
    Examples: "SOFTWARE.VERSION()", "REGISTER(PC)", "sYmbol.BEGIN(main)"

    Args:
        expression: TRACE32 PRACTICE function or expression to evaluate

    Returns:
        Evaluation result as a string
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"EVAL {expression}")
        try:
            result = dbg.fnc.eval_string()
            return f"Result: {result}"
        except Exception:
            try:
                result = dbg.fnc.eval_int()
                return f"Result: {result} (0x{result:X})"
            except Exception:
                return "Expression evaluated (result type not readable via this interface)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Evaluation error '{expression}': {e}"
