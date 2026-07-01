# DebugForge Autonomous Debug Workflow

> Place this file in your project's `CLAUDE.md` or AI agent configuration to enable
> the autonomous debug loop. The AI agent will follow these phases when debugging.

## Instructions for AI Agent

When the user describes a bug or asks you to debug an embedded issue, follow this
structured workflow. Use DebugForge MCP tools at each step.

---

## Phase 1: Understand the Problem

1. Parse the user's bug description — extract key symptoms, error messages, and context
2. Call `get_project_config()` to learn the project setup (ELF, MAP, toolchain, scripts)
3. Call `search_debug_skills(keywords)` with symptom keywords to find matching debug experience
4. If a matching skill exists, call `get_debug_skill(name)` and follow its strategy

## Phase 2: Analyze the Code

5. Read the relevant source files to understand the code logic around the suspected area
6. If needed, call `analyze_map()` to understand memory layout and section sizes
7. If needed, call `disassemble(function)` to inspect critical code at assembly level
8. If needed, call `analyze_elf()` to check ELF structure (sections, symbols)
9. Form a hypothesis about the root cause

## Phase 3: Debug on Hardware

10. Call `build_flash_run()` to compile, download, and start execution
    - If build fails, fix the compile error first and retry
11. Based on your hypothesis, set appropriate breakpoints:
    - `set_breakpoint()` — for code path verification
    - `set_conditional_breakpoint()` — for specific condition triggers
    - `set_data_breakpoint()` — for memory corruption detection
12. Call `go()` to run, then inspect state when stopped:
    - `get_callstack()` — verify execution path
    - `get_locals()` — check variable values
    - `read_variable()` / `read_memory()` — inspect specific data
    - `get_disassembly()` — check actual instructions
13. Analyze the collected data — does it confirm or refute your hypothesis?
14. If hypothesis is wrong, form a new one and repeat from step 11

## Phase 4: Fix and Verify

15. Once root cause is confirmed, modify the source code to fix the bug
16. Call `build_flash_run()` to rebuild, reflash, and run
17. Verify the fix:
    - Set breakpoint at the previously-failing location
    - Check that the problematic condition no longer occurs
    - Run past the failure point to confirm normal execution continues
18. If the fix doesn't work, go back to Phase 3 with adjusted hypothesis

## Phase 5: Knowledge Capture

19. If this is a new debugging pattern worth saving, call `save_debug_skill()` with:
    - The symptoms you observed
    - The debug strategy that worked
    - The root cause you found
    - The fix pattern you applied
20. Report to the user:
    - Root cause explanation
    - What was fixed and how
    - Verification results
    - Any follow-up recommendations

---

## Tips for Effective Debugging

- **Start broad, then narrow**: First understand WHAT is failing, then WHERE, then WHY
- **Use conditional breakpoints**: Avoid stopping on every iteration — target the specific case
- **Check the obvious first**: Clock enabled? Pin configured? Memory aligned?
- **Compare expected vs actual**: Read the register/variable, compare with what the code intended
- **Don't assume — verify**: Even if the code "looks correct", check actual hardware state
- **Binary search for timing issues**: If the bug is intermittent, use count breakpoints to narrow down
