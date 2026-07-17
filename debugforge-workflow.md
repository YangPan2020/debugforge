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

## Phase 6: TRAP / Exception Analysis

When the target has already stopped at a TRAP or exception handler (e.g.
`tricore_exception_handler`, `HardFault_Handler`), follow this specialized
workflow. **Do NOT reset or re-flash — attach and read the live state.**

### Step 1: Attach (Read-Only)

- Call `connect()` — if the default protocol fails, try the other
  (NETASSIST → UDP, NETTCP → TCP)
- Call `get_state()` — confirm the CPU is halted

### Step 2: Capture the Scene

- Call `capture_trap()` — one-shot retrieval of all trap-critical info:
  - CPU state (running/halted, system mode)
  - Key registers (PC, PSW, and architecture-specific registers)
  - Current source location (function, file, line)
  - Full call stack with locals (`Frame.view /Locals /Caller`)
  - Disassembly around PC
  - PSW bitfield analysis (IO, IS, CDC)
- If `capture_trap()` is unavailable, call the individual tools:
  - `get_callstack()` — the call stack shows the faulting call chain
  - `get_source_location()` — where the CPU is now (usually exception handler)
  - `read_register("PC")`, `read_register("PSW")` — key registers
  - `get_disassembly()` — instructions around the faulting address
  - `read_memory()` — trap_info structure, peripheral status registers
  - `read_string()` — read assert filename/message from memory

### Step 3: Identify the Trap Type

Parse the trap class and ID from registers or trap_info structure:

- **TriCore AURIX** (TC3xx):
  - Class 4, TIN 2 → Bus Error (invalid memory access)
  - Class 1 → Internal Protection (privileged instruction, stack overflow)
  - Class 3 → Instruction Error (illegal opcode)
  - `trap_info` structure at A4: `{tAddr, tId, tClass, tCpu}`
- **ARM Cortex-M**:
  - Read SCB fault status registers (CFSR, HFSR, MMFAR, BFAR)
  - `read_memory("0xE000ED28", 16)` for fault status

### Step 4: Find the Faulting Instruction

- The `trap_info.tAddr` field (or stacked PC in ARM exception frame) points to
  the instruction that triggered the trap — this is NOT the current PC (which
  is in the exception handler)
- Call `get_disassembly(address)` at the faulting address to see the offending
  instruction (typically a `ld`/`st` with an invalid pointer)

### Step 5: Walk the Call Stack

- The call stack from `get_callstack()` reveals the full fault path:
  - Top: exception handler (dead loop or trap return)
  - Middle: trap entry → faulting function
  - Bottom: the ISR or task that triggered the faulting call chain
- Look for `assert` / `DEBUGASSERT` in the stack — this indicates a
  failed condition check, not a direct hardware fault. The assert macro
  name varies by RTOS (e.g. `DEBUGASSERT` in NuttX, `assert_param` in
  FreeRTOS, `configASSERT` in FreeRTOS+TCP).
- If assert is present, use `read_string()` on the filename pointer to get
  the source file and line number of the failing assertion

### Step 6: Cross-Reference with ELF

- Call `disassemble(function)` to get static disassembly from the ELF
- Compare with the dynamic disassembly from TRACE32 — they should match
- Use `analyze_elf("symbols")` to find function addresses and sizes
- Cross-reference trap address with symbol table to confirm the function

### Step 7: Analyze Root Cause

Common patterns:

1. **Stack overflow / interrupt nesting overflow** → stack too small for
   interrupt nesting depth, corrupted context leads to secondary fault
   - Check RTOS configuration for interrupt stack size and nesting limits
   - Compare against actual nesting depth observed in the call stack
2. **Assert failure (secondary trap)** → a runtime condition check failed,
   the assert handler itself may crash due to corrupted state
   - Read the assert file:line to see the failing condition
   - Check the configuration value that the condition compares against
3. **Null pointer dereference** → uninitialized or freed pointer
4. **MPU violation** → access to protected memory region

### Step 8: Fix and Re-verify

- Modify the configuration or source code
- Call `build_flash_run()` to rebuild, reflash, and run
- Monitor for an extended period to confirm the trap no longer occurs
- Save the experience as a debug skill

---

## Tips for Effective Debugging

- **Start broad, then narrow**: First understand WHAT is failing, then WHERE, then WHY
- **Use conditional breakpoints**: Avoid stopping on every iteration — target the specific case
- **Check the obvious first**: Clock enabled? Pin configured? Memory aligned?
- **Compare expected vs actual**: Read the register/variable, compare with what the code intended
- **Don't assume — verify**: Even if the code "looks correct", check actual hardware state
- **Binary search for timing issues**: If the bug is intermittent, use count breakpoints to narrow down
