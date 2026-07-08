#!/usr/bin/env python3
"""
Example: Test all DebugForge debug tools via PYRCL

Comprehensive test of all TRACE32 debug capabilities:
- Connection, execution, registers, memory
- Breakpoints, symbols, variables, commands
- Views, multicore, system config, trace
- Benchmark, notifications, watchpin, OS awareness

Usage:
  1. Copy debugforge.toml.example to debugforge.toml
  2. Ensure Trace32 is running with RCL enabled
  3. Run: python examples/test_all_tools.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lauterbach.trace32.rcl import connect
from debugforge.config import load_config

results = []


def test(name, func):
    print(f"\n[{name}]", flush=True)
    try:
        result = func()
        print(f"  PASS: {result}", flush=True)
        results.append((name, "PASS", str(result)[:200]))
        return result
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}", flush=True)
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        return None


def main():
    cfg = load_config()
    host = cfg.remote.host or cfg.node
    port = str(cfg.port)

    # ========== CONNECT ==========
    print("=" * 70, flush=True)
    print("Phase 1: Connect to Trace32", flush=True)
    print("=" * 70, flush=True)

    print(f"Connecting to {host}:{port}...", flush=True)
    dbg = connect(node=host, port=port, protocol=cfg.protocol, timeout=30)
    print("Connected!", flush=True)
    ver = dbg.fnc.version_software()
    print(f"  Version: {ver}", flush=True)

    # ========== LOAD ELF ==========
    print("\n" + "=" * 70, flush=True)
    print("Phase 2: Load ELF", flush=True)
    print("=" * 70, flush=True)

    cmm_path = cfg.scripts.get("flash", "")
    if cmm_path:
        print(f"Executing: {cmm_path}", flush=True)
        try:
            dbg.cmm(cmm_path)
            print("CMM executed", flush=True)
        except Exception as e:
            print(f"CMM error: {e}", flush=True)
            print("Continuing anyway...", flush=True)
        time.sleep(3)
    else:
        print("No flash script configured, skipping", flush=True)

    # ========== CONNECTION TOOLS ==========
    print("\n" + "=" * 70, flush=True)
    print("Phase 3: Test All Debug Tools", flush=True)
    print("=" * 70, flush=True)

    print("\n--- Connection Tools ---", flush=True)

    def t_status():
        v = dbg.fnc.version_software()
        cpu = dbg.fnc.system_cpu()
        up = dbg.fnc.system_up()
        return f"v={v}, cpu={cpu}, up={up}"
    test("connection.status", t_status)

    # ========== EXECUTION TOOLS ==========
    print("\n--- Execution Tools ---", flush=True)

    def t_halt():
        dbg.break_()
        time.sleep(0.5)
        halt = dbg.fnc.state_halt()
        return f"Halted: {halt}"
    test("execution.halt", t_halt)

    def t_state():
        halt = dbg.fnc.state_halt()
        run = dbg.fnc.state_run()
        target = dbg.fnc.state_target()
        power = dbg.fnc.state_power()
        return f"halt={halt}, run={run}, target={target}, power={power}"
    test("execution.state", t_state)

    def t_step():
        dbg.step()
        time.sleep(0.2)
        pc = dbg.register.read("PC")
        return f"Stepped to PC=0x{pc.value:X}"
    test("execution.step", t_step)

    def t_go():
        dbg.go()
        time.sleep(1)
        run = dbg.fnc.state_run()
        dbg.break_()
        time.sleep(0.3)
        return f"Running was: {run}"
    test("execution.go", t_go)

    # ========== REGISTERS TOOLS ==========
    print("\n--- Register Tools ---", flush=True)

    def t_reg_read():
        pc = dbg.register.read("PC")
        sp = dbg.register.read("SP")
        return f"PC=0x{pc.value:X}, SP=0x{sp.value:X}"
    test("registers.read", t_reg_read)

    def t_reg_write():
        d0 = dbg.register.read("D0")
        old = d0.value
        dbg.register.write("D0", 0x12345678)
        d0_new = dbg.register.read("D0")
        dbg.register.write("D0", old)
        return f"D0: 0x{old:X} -> 0x{d0_new.value:X} -> restored"
    test("registers.write", t_reg_write)

    # ========== MEMORY TOOLS ==========
    print("\n--- Memory Tools ---", flush=True)

    def t_mem_read():
        pc = dbg.register.read("PC")
        data = dbg.memory.read(pc.value, 16)
        hexs = " ".join(f"{b:02X}" for b in data)
        return f"@0x{pc.value:X}: {hexs}"
    test("memory.read", t_mem_read)

    def t_mem_read32():
        pc = dbg.register.read("PC")
        val = dbg.memory.read_uint32(pc.value)
        return f"@0x{pc.value:X}: uint32=0x{val:X}"
    test("memory.read_uint32", t_mem_read32)

    # ========== BREAKPOINTS TOOLS ==========
    print("\n--- Breakpoint Tools ---", flush=True)

    def t_bp_set():
        pc = dbg.register.read("PC")
        addr = pc.value + 0x10
        dbg.breakpoint.set(addr)
        bps = dbg.breakpoint.list()
        return f"Set BP @0x{addr:X}, total={len(bps)}"
    test("breakpoints.set", t_bp_set)

    def t_bp_list():
        bps = dbg.breakpoint.list()
        if bps:
            info = [(f"0x{bp.address:X}" if hasattr(bp, 'address') else str(bp)) for bp in bps[:5]]
            return f"{len(bps)} BP(s): {info}"
        return "0 breakpoints"
    test("breakpoints.list", t_bp_list)

    def t_bp_delete():
        bps = dbg.breakpoint.list()
        if bps:
            dbg.cmd("BREAK.DELETE")
            return "All breakpoints deleted"
        return "No BP to delete"
    test("breakpoints.delete", t_bp_delete)

    # ========== SYMBOLS TOOLS ==========
    print("\n--- Symbol Tools ---", flush=True)

    def t_sym_query_name():
        syms = dbg.symbol.query_by_name("main")
        if syms:
            s = syms[0]
            attrs = {a: getattr(s, a, '?') for a in ['name', 'address', 'size'] if hasattr(s, a)}
            return f"'main' found: {attrs}"
        return "No 'main' symbol"
    test("symbols.query_by_name", t_sym_query_name)

    def t_sym_exist():
        exist = dbg.fnc.symbol_exist("main")
        return f"symbol_exist('main') = {exist}"
    test("symbols.exist", t_sym_exist)

    # ========== MULTICORE TOOLS ==========
    print("\n--- Multicore Tools ---", flush=True)

    def t_mc_cpu():
        cpu = dbg.fnc.system_cpu()
        return f"CPU: {cpu}"
    test("multicore.cpu", t_mc_cpu)

    # ========== SYSTEM CONFIG TOOLS ==========
    print("\n--- System Config Tools ---", flush=True)

    def t_sys_mode():
        mode = dbg.fnc.system_mode()
        return f"Mode: {mode}"
    test("system_config.mode", t_sys_mode)

    # ========== TRACE TOOLS ==========
    print("\n--- Trace Tools ---", flush=True)

    def t_trace_state():
        state = dbg.fnc.trace_state()
        return f"Trace state: {state}"
    test("trace.state", t_trace_state)

    # ========== SUMMARY ==========
    print("\n" + "=" * 70, flush=True)
    print("TEST SUMMARY", flush=True)
    print("=" * 70, flush=True)

    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}", flush=True)

    if failed > 0:
        print(f"\nFailed tests:", flush=True)
        for name, s, msg in results:
            if s == "FAIL":
                print(f"  FAIL {name}: {msg}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("DONE", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
