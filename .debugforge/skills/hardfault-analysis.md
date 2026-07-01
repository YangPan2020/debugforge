---
name: hardfault-analysis
category: fault
severity: critical
keywords:
  - HardFault
  - BusFault
  - UsageFault
  - exception
  - trap
  - crash
---

# HardFault / Exception Analysis

## Symptoms
- Target stops unexpectedly in a fault handler (HardFault, BusFault, etc.)
- Program counter (PC) jumps to exception vector
- System hangs or watchdog resets

## Debug Strategy

### Step 1: Identify the fault type
- get_state() — confirm target is in exception/fault state
- read_register("PC") — check if in fault handler
- For ARM Cortex-M: read_memory("0xE000ED28", 16) — SCB fault status registers
- For TriCore: read_register("PCXI") and check trap vector

### Step 2: Find the faulting instruction
- get_callstack() — the return address in the fault frame points to the offending instruction
- For Cortex-M: stacked PC is at SP+24 in the exception frame
- For TriCore: check CSA (Context Save Area) chain via PCXI

### Step 3: Analyze the cause
- disassemble() at the faulting PC address
- read_memory() at the accessed address (for BusFault/MemManage)
- Check MPU configuration if MemManage fault
- Check alignment for UsageFault (unaligned access)

### Step 4: Reproduce deterministically
- set_breakpoint at the instruction BEFORE the faulting one
- Inspect all relevant registers and memory at that point
- Trace back to find what set up the invalid state

## Common Root Causes
1. Null pointer dereference (access to address 0x0)
2. Use-after-free (accessing freed heap memory)
3. Unaligned memory access (on architectures that don't support it)
4. Invalid function pointer call (corrupted vtable or callback)
5. MPU violation (accessing protected memory region)
6. Stack overflow corrupting return address
7. Division by zero (UsageFault on some architectures)

## Fix Patterns
1. Add null-pointer checks before dereference
2. Use memory sanitizers or guard patterns for heap
3. Ensure proper alignment with __attribute__((aligned))
4. Validate function pointers before calling
5. Review MPU configuration for the accessed region
6. Enable all configurable fault handlers (not just HardFault)
