---
name: trap-analysis
category: fault
severity: critical
keywords:
  - TRAP
  - Bus Error
  - exception
  - crash
  - fault handler
  - assert
  - stack overflow
  - interrupt nesting
  - CSA corruption
  - null pointer
  - MPU violation
---

# TRAP / Exception Analysis

## Symptoms

- Target stops unexpectedly in a trap or exception handler
- Program counter is in a fault handler (e.g. `HardFault_Handler`,
  `tricore_exception_handler`, or equivalent)
- System crashes under load, after running normally for a period
- Call stack shows a fault chain through assert/dump handlers

## Debug Strategy

### Step 1: Capture the trap scene
- `capture_trap()` — get registers, call stack, disassembly at once
- Confirm: CPU is halted, PC is in exception handler
- If `capture_trap()` is unavailable, use individual tools:
  - `get_state()` — confirm halted
  - `read_register("PC")`, `read_register("PSW")` — key registers
  - `get_callstack()` — fault chain
  - `get_source_location()` — current function/file/line

### Step 2: Identify the trap type

Parse trap class and ID from registers or trap_info structure:

- **TriCore AURIX** (TC3xx):
  - Class 4 → Bus Error (invalid memory access)
  - Class 1 → Internal Protection (privileged instruction, stack overflow)
  - Class 3 → Instruction Error (illegal opcode)
  - `trap_info` structure: `{tAddr, tId, tClass, tCpu}`
- **ARM Cortex-M**:
  - Read SCB fault status registers (CFSR, HFSR, MMFAR, BFAR)
  - `read_memory("0xE000ED28", 16)` for fault status
- **Other architectures**: consult the vendor's exception/fault documentation

### Step 3: Find the faulting instruction
- The trap/fault entry address (trap_info.tAddr or stacked PC) points to
  the instruction that triggered the trap — this is NOT the current PC
  (which is in the exception handler)
- `get_disassembly(address)` at the faulting address — typically a
  load/store with an invalid pointer

### Step 4: Walk the call stack
- `get_callstack()` reveals the full fault path:
  - Top: exception handler (often a dead loop)
  - Middle: trap entry → faulting function
  - Bottom: the ISR or task that triggered the faulting call chain
- Look for `assert` in the stack (macro name varies by RTOS — e.g.
  `DEBUGASSERT` in NuttX, `assert_param` in FreeRTOS) — indicates a failed
  condition check, not a direct hardware fault
- If assert is present, use `read_string()` on the filename pointer
  to read the source file path and line number of the failing assertion

### Step 5: Cross-reference with ELF
- `disassemble(function)` — confirm the faulting instruction matches
  the static disassembly from the ELF
- `analyze_elf("symbols")` — find function addresses and sizes
- Cross-reference trap address with symbol table to confirm the function

### Step 6: Analyze root cause

Identify which pattern applies:

1. **Stack overflow / interrupt nesting overflow**
   - Stack too small for interrupt nesting depth → corrupted context
     → secondary fault in stack/fault traversal code
   - Check RTOS config for interrupt stack size and nesting limits
2. **Assert failure (secondary trap)**
   - A runtime condition check failed, triggering the assert handler
   - The assert handler itself may crash (e.g. stack traversal with
     corrupted state) — the trap is a secondary failure
   - Read the assert file:line to see the failing condition
3. **Null pointer dereference** — uninitialized or freed pointer
4. **MPU violation** — access to protected memory region
5. **Illegal instruction** — corrupted code, bad function pointer

### Step 7: Fix and re-verify
- Modify the configuration or source code based on root cause
- `build_flash_run()` — rebuild, reflash, and run
- Monitor for an extended period to confirm the trap no longer occurs
- `save_debug_skill()` — capture the experience for future reuse

## Common Root Causes

1. Stack size insufficient for actual interrupt nesting depth
2. Assert handler crashing due to corrupted state during error handling
3. High-frequency interrupts causing rapid re-entry before ISR completes
4. Null pointer dereference (uninitialized, freed, or overwritten)
5. Invalid function pointer call (corrupted vtable or callback)
6. Unaligned memory access on architectures that don't support it
7. MPU/memory protection region misconfiguration

## Fix Patterns

1. Increase interrupt stack size in RTOS configuration
2. Review and adjust interrupt priority assignments to reduce nesting
3. Add pointer validation before dereferencing in fault/assert handlers
4. Add null-pointer checks before access in faulting code paths
5. Ensure proper alignment with compiler attributes
6. Review MPU region configuration for the accessed memory area
7. Disable nested interrupts during assert/dump processing to reduce
   stack pressure during error handling
