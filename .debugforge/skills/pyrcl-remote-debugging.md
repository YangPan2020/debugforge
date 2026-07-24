---
name: pyrcl-remote-debugging
category: general
severity: info
keywords:
  - PYRCL
  - remote debug
  - RCL
  - NETTCP
  - network drive
  - config.t32
  - firewall
  - Trace32
---

# PYRCL Remote Debugging Known Issues & Solutions

Known issues and solutions for remote TRACE32 debugging via PYRCL.

## Issue 1: PYRCL Cannot See Network Drive (Y:)

**Symptom**: `DO Y:\...\script.cmm` or `Data.LOAD.Elf Y:\...\firmware.elf`
reports `file not found`, but manual execution in Trace32 command line succeeds.

**Root Cause**: Network drive mappings are user-session level (HKCU\Network\Y).
PYRCL executes commands via RCL protocol in a background thread with a different
file system context that cannot see Y: drive.

**Solutions** (by priority):

1. **Copy files to remote C: drive** (most reliable)
   ```
   C:\Users\<user>\Documents\<project>\
   ```

2. **Use UNC path** (no network drive mapping needed)
   ```
   \\<REMOTE_IP>\<share_name>\<project>\...
   ```

3. **Configure path mapping in debugforge.toml**
   ```toml
   [[remote.source_translates]]
   from = "Y:\\<project>"
   to = "\\\\<REMOTE_IP>\\<share_name>\\<project>"
   ```

## Issue 2: run_cmm_script / run_practice DO Duplication

**Symptom**: `run_cmm_script` reports
`file C:\T32\bin\windows64\DO.cmm not found`

**Root Cause**: PYRCL's `dbg.cmm(script)` method internally adds a `DO` prefix,
combined with the tool's own prefix, resulting in `DO DO "script.cmm"`.

**Solution**: Use `execute_command` instead of `run_cmm_script`
```python
# Wrong: becomes DO DO "..."
run_cmm_script("Y:\\path\\script.cmm")

# Correct: direct execute_command
execute_command('DO Y:\\path\\script.cmm')
```

## Issue 3: TriCore step Triggers Interrupt Exception

**Symptom**: After `step`, PC jumps to interrupt vector table (0x80404xxx),
CPU stops in interrupt handler, all subsequent operations fail,
requires SYStem.Up to reconnect.

**Root Cause**: TriCore interrupt response is triggered during single-step,
PC jumps to interrupt vector.

**Solution**: Use `go_till` instead of `step`
```python
# Error-prone: triggers exception
step(mode="over")

# Safe: run to specific address
go_till(address="target_function")
```

## Issue 4: config.t32 Without RCL Configuration

**Symptom**: PYRCL connection timeout, but ping succeeds.

**Root Cause**: Trace32 started with config.t32 that has no RCL configuration,
port 20000 not listening.

**Solution**: Append RCL configuration to config.t32 (non-destructive)
```
RCL=NETTCP
PORT=20000
PACKLEN=4096
```
Or start with config_auto.t32:
```cmd
"C:\T32\bin\windows64\t32mtc.exe" -c "C:\T32\config_auto.t32"
```

## Issue 5: Windows Firewall Blocks RCL Port

**Symptom**: Ping succeeds, SMB (445) open, but TCP 20000 times out.

**Solution**: Run as administrator on remote machine
```powershell
New-NetFirewallRule -DisplayName "TRACE32 RCL" -Direction Inbound -Protocol TCP -LocalPort 20000 -Action Allow
```

## Efficient Debug Workflow

### Inefficient Flow (~50 tool calls)
```
connect → load → set bp → go → get_state → read_var → write_var → go → ...
```

### Optimized Flow (~10 tool calls)

1. **Pre-calculate** (local execution, zero tokens)
   ```bash
   nm <elf> | grep "function_name"
   objdump -d --start-address=0xNNNN --stop-address=0xNNNN+4 <elf>
   ```

2. **One-shot connect** (1 call)
   ```python
   connect(node, port, protocol)
   execute_command('Data.LOAD.Elf "<path>" /NoCode /ALTBITFIELDS')
   clear_all_breakpoints()
   ```

3. **action breakpoint** (1 call)
   ```python
   set_action_breakpoint(address=<addr>, command='Var.set <var> <val>', resume=True)
   ```

4. **go_till to deepest** (1 call)
   ```python
   go_till(address="deepest_function")
   ```

5. **capture_trap** (if needed)
   ```python
   capture_trap()
   ```

## TriCore Stack Frame Instruction Reference

| Instruction | Frame Size | Scope |
|-------------|-----------|-------|
| `sub16.a a10,#0xNN` | NN (hex) bytes | Small frames (≤255B) |
| `lea a10,[a10]-0xNNNN` | NNNN (hex) bytes | Large frames (>255B) |
| No `sub SP` | 0 bytes | wrapper/inline function |

Examples:
- `sub16.a a10,#0x18` → 24B
- `sub16.a a10,#0x78` → 120B
- `lea a10,[a10]-0xB78` → 2936B
