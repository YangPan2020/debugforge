"""Workflow orchestration tools — composite debug operations."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import config, state


@mcp.tool()
async def flash_and_run(break_at: str = "main") -> str:
    """Flash firmware to target and run to a breakpoint (default: main).

    Composite operation:
      1. Execute the configured flash script (downloads firmware)
      2. Reset the target
      3. Set a breakpoint at the specified symbol
      4. Run to that breakpoint

    Args:
        break_at: Symbol to break at after flashing (default: "main"). Set empty to skip.

    Returns:
        Step-by-step execution results
    """
    dbg = state.require_connection()
    results = []

    # Step 1: Flash
    flash_script = config.scripts.get("flash", "")
    if not flash_script:
        return "Error: No flash script configured. Set [scripts] flash in debugforge.toml"

    try:
        dbg.cmm(flash_script, timeout=120.0)
        results.append(f"1. Flash completed: {flash_script}")
    except TimeoutError:
        return f"Flash timed out (120s): {flash_script}"
    except Exception as e:
        return f"Flash failed: {e}"

    # Step 2: Reset
    try:
        dbg.cmd("SYStem.Up")
        results.append("2. Target reset (SYStem.Up)")
    except Exception as e:
        results.append(f"2. Reset warning: {e}")

    # Step 3 & 4: Set breakpoint and run
    if break_at:
        try:
            dbg.cmd(f"Break.Set {break_at}")
            results.append(f"3. Breakpoint set at: {break_at}")
        except Exception as e:
            results.append(f"3. Breakpoint warning: {e}")

        try:
            dbg.cmd("Go")
            results.append(f"4. Running — will stop at {break_at}")
        except Exception as e:
            results.append(f"4. Run warning: {e}")
    else:
        results.append("3. No breakpoint set (break_at is empty)")

    return "\n".join(results)


@mcp.tool()
async def build_flash_run(break_at: str = "main") -> str:
    """Full cycle: build the project, flash firmware, and run to breakpoint.

    Composite operation:
      1. Build the project (compile)
      2. Flash the firmware to target
      3. Reset and run to the specified breakpoint

    This is the core "edit-compile-debug" loop tool.

    Args:
        break_at: Symbol to break at after flashing (default: "main")

    Returns:
        Step-by-step results for the entire build-flash-run cycle
    """
    # Step 1: Build
    from debugforge.tools.build import build_project
    build_result = await build_project()
    if "FAILED" in build_result:
        return f"Build failed — aborting flash.\n\n{build_result}"

    results = [build_result, ""]

    # Step 2 & 3: Flash and run
    flash_result = await flash_and_run(break_at=break_at)
    results.append(flash_result)

    return "\n".join(results)
