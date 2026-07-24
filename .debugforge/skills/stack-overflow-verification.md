---
name: stack-overflow-verification
category: memory
severity: critical
keywords:
  - stack overflow
  - WCSU
  - worst case stack usage
  - stack frame
  - sub SP
  - call chain
  - trap
---

# Stack Overflow Verification (WCSU Validation)

Verify whether static stack analysis (WCSU - Worst Case Stack Usage) is reliable,
and detect if the worst-case call path actually causes a stack overflow trap.

## Symptoms
- Static analysis reports WCSU exceeds allocated stack size (e.g., 9048B vs 1024B)
- Need to confirm whether the worst-case path is actually reachable
- Need to verify if stack overflow trap actually occurs at runtime

## Debug Strategy (6-Step Method)

### Step 1: Pre-calculate Stack Frames (Local, Zero Tokens)

Use `nm` + `objdump` locally to batch-extract stack frame sizes.
**Do NOT use the debugger to disassemble each function one by one** —
that wastes tokens.

```bash
# Extract function addresses
nm <elf_file> | grep -E "func1|func2|func3"

# Batch-extract sub SP instructions for all functions
for addr in 0xAAAA 0xBBBB 0xCCCC; do
    objdump -d --start-address=$addr --stop-address=$(($addr+4)) <elf_file> | grep "sub\|lea.*a10"
done
```

**TriCore Stack Frame Instruction Reference**:
- `sub16.a a10,#0xNN` → frame = NN (hex) bytes (small frames ≤255B)
- `lea a10,[a10]-0xNNNN` → frame = NNNN (hex) bytes (large frames >255B)
- No `sub SP` → 0 bytes (wrapper/inline function)

### Step 2: Source-Level Condition Analysis

```bash
# Locate worst-path condition branches
grep -n "if.*condition" <source_file.c>

# Find enum/define values
grep -rn "define.*ENUM_NAME" <include_dir>/

# Find call chain
grep -rn "function_name" <source_dir>/
```

### Step 3: One-Shot Connect + Load Symbols

```python
# Complete connect + symbol load + breakpoint clear in one pass
connect(node="<REMOTE_IP>", port=20000, protocol="TCP")
execute_command('Data.LOAD.Elf "<REMOTE_LOCAL_PATH>" /NoCode /ALTBITFIELDS')
clear_all_breakpoints()
```

**Key**: Use remote local path (C:\...), NOT network drive (Y:).
PYRCL cannot see user-session network drive mappings.

### Step 4: Action Breakpoint for Auto Condition Modification

```python
# Set action breakpoint at condition check point
# Auto-modify variable on hit, then resume execution
set_action_breakpoint(
    address=<condition_check_addr>,
    command='Var.set <variable> <value>',
    resume=True
)

# Batch-modify all condition variables at task entry
set_breakpoint(address="<task_function>")
# When hit, modify all conditions at once:
write_variable("<var1>", <value1>)
write_variable("<var2>", <value2>)
```

### Step 5: Stack Overflow Detection

**Method A: Data Breakpoint on Stack Bottom (Recommended)**
```python
# Set write breakpoint at stack bottom address
# When SP drops below stack bottom, write triggers = overflow confirmed
set_data_breakpoint(address=<stack_bottom_addr>, access="write")
```

**Method B: go_till to Deepest Function**
```python
# Run to the deepest function in worst-case path
go_till(address="<deepest_function>")
# Check SP against stack bottom
read_register("A10")  # SP on TriCore
```

### Step 6: Trap Capture

```python
# If stack overflow causes a trap, CPU will stop
capture_trap()
# Returns: registers, call stack, disassembly, PSW analysis
```

## Common Root Causes
1. Deep call chain with large stack frames (especially nested register-read functions)
2. Large local arrays in deep functions (e.g., char buf[2936] on stack)
3. Conditional path reachable only in specific product variant (e.g., VC version)
4. Stack size allocated for normal case, not accounting for worst-case path

## Fix Patterns
1. Increase task stack size to WCSU + safety margin (e.g., 10240B for 9048B WCSU)
2. Move large local buffers from stack to heap/static storage
3. Refactor large-frame functions to use dynamic allocation
4. Add stack guard region with MPU for runtime overflow detection
5. Use `Var.STACKUSE` in TRACE32 to measure actual high-water mark

## Key Lessons
1. **Pre-calculate > dynamic debug** — nm+objdump locally costs zero tokens
2. **action breakpoint > manual modify** — avoids per-cycle variable reset
3. **go_till > step** — step triggers TriCore interrupt exception
4. **UNC path > Y: drive** — PYRCL cannot see network drive mappings
5. **execute_command('DO ...') > run_cmm_script** — avoids DO-prefix duplication
