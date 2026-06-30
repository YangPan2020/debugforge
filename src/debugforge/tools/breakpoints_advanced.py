"""Advanced breakpoint tools — conditional, data value, count, task-specific, action breakpoints."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state


@mcp.tool()
async def set_conditional_breakpoint(
    address: str,
    condition: str,
    language: str = "hll",
) -> str:
    """Set a conditional breakpoint that only stops when a condition is true.

    Args:
        address: Address or symbol (e.g., "main", "0x80001000", "sieve\\11")
        condition: Condition expression.
                   HLL example: "(counter > 10) && (flag == 1)"
                   TRACE32 example: "Register(D0)>5"
        language: "hll" for C/C++ syntax, "t32" for TRACE32 PRACTICE syntax

    Returns:
        Confirmation of conditional breakpoint
    """
    dbg = state.require_connection()
    try:
        if language == "hll":
            cmd = f"Var.Break.Set {address} /Program /VarCONDition ({condition})"
        else:
            cmd = f"Break.Set {address} /Program /CONDition {condition}"
        dbg.cmd(cmd)
        return f"Conditional breakpoint set at {address} (condition: {condition})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting conditional breakpoint: {e}"


@mcp.tool()
async def set_data_breakpoint(
    address: str,
    access: str = "write",
    data_value: str = "",
    data_width: str = "long",
) -> str:
    """Set a data breakpoint that triggers on memory read/write access, optionally matching a value.

    Args:
        address: Variable name or memory address (e.g., "myVar", "0xD0000100")
        access: Access type — "read", "write", or "readwrite"
        data_value: Optional data value to match (e.g., "0x33", "0x0"). Empty = any value.
        data_width: Width for value matching — "byte", "word", "long", "quad", "auto"

    Returns:
        Confirmation of data breakpoint
    """
    dbg = state.require_connection()
    try:
        access_map = {"read": "/Read", "write": "/Write", "readwrite": "/ReadWrite"}
        access_flag = access_map.get(access)
        if not access_flag:
            return f"Invalid access type '{access}'. Use: read, write, readwrite"

        cmd = f"Break.Set {address} {access_flag}"
        if data_value:
            width_map = {
                "byte": "Byte", "word": "Word", "long": "Long",
                "quad": "Quad", "auto": "auto",
            }
            w = width_map.get(data_width, "Long")
            cmd += f" /DATA.{w} {data_value}"

        dbg.cmd(cmd)
        msg = f"Data breakpoint set: {access} @ {address}"
        if data_value:
            msg += f" (value={data_value}, width={data_width})"
        return msg
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting data breakpoint: {e}"


@mcp.tool()
async def set_count_breakpoint(
    address: str,
    count: int,
    impl: str = "auto",
) -> str:
    """Set a count breakpoint that stops after N-th hit.

    Useful for breaking in a loop at a specific iteration.

    Args:
        address: Address or symbol name
        count: Number of hits before stopping (e.g., 100 = stop on 100th hit)
        impl: "auto", "soft" (software counter, intrusive), or "hard" (on-chip counter, real-time)

    Returns:
        Confirmation of count breakpoint
    """
    dbg = state.require_connection()
    try:
        impl_map = {"auto": "", "soft": " /SOFT", "hard": " /Onchip"}
        impl_flag = impl_map.get(impl, "")
        cmd = f"Break.Set {address} /Program{impl_flag} /COUNT {count}."
        dbg.cmd(cmd)
        return f"Count breakpoint set at {address} (stop on hit #{count})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting count breakpoint: {e}"


@mcp.tool()
async def set_task_breakpoint(
    address: str,
    task: str,
) -> str:
    """Set a task-specific breakpoint that only triggers for a specific OS task/thread.

    Requires OS-awareness to be configured.

    Args:
        address: Address or symbol name
        task: Task identifier — name (e.g., "idle_task"), ID (e.g., "14"), or magic number

    Returns:
        Confirmation of task breakpoint
    """
    dbg = state.require_connection()
    try:
        if task.startswith("0x") or task.startswith("0X"):
            task_ref = task
        elif task.isdigit():
            task_ref = f"{task}."
        else:
            task_ref = f'"{task}"'
        cmd = f"Break.Set {address} /Program /TASK {task_ref}"
        dbg.cmd(cmd)
        return f"Task breakpoint set at {address} (task: {task})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting task breakpoint: {e}"


@mcp.tool()
async def set_action_breakpoint(
    address: str,
    command: str,
    resume: bool = True,
) -> str:
    """Set an action breakpoint that executes a TRACE32 command when hit.

    The target briefly stops, the command executes, then optionally resumes.
    Useful for logging variable values, collecting trace data, etc.

    Args:
        address: Address or symbol name
        command: TRACE32 command to execute on hit (e.g., "Var.print counter")
        resume: True to auto-resume after command (default), False to stay stopped

    Returns:
        Confirmation of action breakpoint
    """
    dbg = state.require_connection()
    try:
        resume_flag = "/RESUME" if resume else ""
        escaped_cmd = command.replace('"', '""')
        cmd = f'Break.Set {address} /Program /CMD "{escaped_cmd}" {resume_flag}'
        dbg.cmd(cmd)
        action = "resume after" if resume else "stop at"
        return f"Action breakpoint set at {address} (cmd: {command}, {action})"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting action breakpoint: {e}"


@mcp.tool()
async def set_temporary_breakpoint(address: str) -> str:
    """Set a temporary breakpoint that auto-deletes after first hit.

    Equivalent to "run to this address once".

    Args:
        address: Address or symbol name

    Returns:
        Confirmation
    """
    dbg = state.require_connection()
    try:
        dbg.cmd(f"Break.Set {address} /Program /DeleteHIT")
        return f"Temporary breakpoint set at {address} (will delete on hit)"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error setting temporary breakpoint: {e}"
