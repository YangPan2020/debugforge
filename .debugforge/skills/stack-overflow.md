---
name: stack-overflow
category: memory
severity: critical
keywords:
  - stack overflow
  - HardFault
  - SP corruption
  - MemManage
  - stack pointer
---

# Stack Overflow Detection

## Symptoms
- HardFault or MemManage fault triggered unexpectedly
- Stack Pointer (SP) points to an illegal address range
- Local variables appear corrupted or overwritten
- Crash on function return

## Debug Strategy

### Step 1: Check stack pointer
- read_register("SP") — compare with valid stack range
- symbol_by_name("__stack_start") and symbol_by_name("__stack_end")
- If SP is outside the valid range, stack overflow is confirmed

### Step 2: Analyze call stack depth
- get_callstack() — check for deep nesting or recursion
- get_locals() — look for large local arrays

### Step 3: Analyze stack usage
- analyze_map() with section ".stack" — check configured stack size
- disassemble() suspected functions — check frame size in prologue

### Step 4: Identify the trigger
- set_data_breakpoint on stack guard area (just below stack bottom)
- Run and wait for watchpoint hit — the callstack at that point shows the culprit

## Common Root Causes
1. Recursive function without exit condition or too deep
2. Large local array declarations (e.g., char buf[4096] on stack)
3. Deep interrupt nesting accumulating stack frames
4. Stack-consuming functions called from ISR context
5. Insufficient stack size in linker script configuration

## Fix Patterns
1. Increase stack size in linker script (__stack_size symbol)
2. Move large arrays to static storage or heap
3. Convert deep recursion to iterative approach
4. Add stack overflow detection (MPU guard region or canary pattern)
5. Use TRACE32 Var.STACKUSE to measure actual stack high-water mark
