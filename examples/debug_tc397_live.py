#!/usr/bin/env python3
"""
Example: TC397 automated debug workflow (full pipeline)

Demonstrates complete debug workflow:
1. Connect Trace32 via PYRCL
2. Flash download via CMM script
3. Set breakpoints and run
4. Inspect registers, variables, memory
5. Callstack and source analysis
6. OS awareness (NuttX tasks)
7. Step execution with variable tracking
8. Peripheral register read

Usage:
  1. Copy debugforge.toml.example to debugforge.toml
  2. Configure connection and project paths
  3. Run: python examples/debug_tc397_live.py
"""

from __future__ import annotations

import os
import sys
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lauterbach.trace32.rcl import connect as t32_connect
from debugforge.config import load_config
from debugforge.state import state


def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _read_window(dbg, command: str, max_size: int = 32768) -> str:
    content = bytearray()
    offset = 0
    while True:
        try:
            length, chunk = dbg._get_window_content(command, 4096, offset, "ASCII")
        except Exception:
            break
        if length == 0 or not chunk:
            break
        content += chunk[:length]
        offset += length
        if offset >= max_size:
            break
    return content.decode("utf-8", errors="replace")


def cmd(dbg, c: str):
    print(f"  > {c}")
    try:
        dbg.fnc.error_occurred()
        dbg.cmd(c)
        print(f"    OK")
    except Exception as e:
        print(f"    [WARN] {e}")


def sym_addr(dbg, name: str) -> int | None:
    try:
        s = dbg.symbol.query_by_name(name)
        if s.address and s.address.value is not None:
            return s.address.value
    except Exception:
        pass
    return None


def pc_to_func(dbg, pc: int) -> str:
    try:
        addr = dbg.address.from_string(f"0x{pc:08X}")
        sym = dbg.symbol.query_by_address(addr)
        return sym.name or "(unknown)"
    except Exception:
        return "(unknown)"


def phase1_connect(cfg):
    banner("Phase 1: Connect Trace32")
    print(f"  Config: node={cfg.node}, port={cfg.port}, protocol={cfg.protocol}")
    print(f"  ELF: {cfg.elf}")
    print(f"  Flash script: {cfg.scripts.get('flash', '(none)')}")

    dbg = t32_connect(node=cfg.node, port=cfg.port, protocol=cfg.protocol)
    ver = dbg.fnc.software_version()
    print(f"  Connected, version: {ver}")

    state.debugger = dbg
    state.node = cfg.node
    state.port = cfg.port
    state.protocol = cfg.protocol

    return dbg


def phase2_flash(dbg, cfg):
    banner("Phase 2: Flash Download & JTAG Connect")

    flash_script = cfg.scripts.get("flash", "")
    elf_path = cfg.elf

    if not flash_script:
        print("  [SKIP] No flash script configured, loading symbols only")
        cmd(dbg, f'Data.LOAD.Elf "{elf_path}" /NoCODE')
        return

    print(f"  Flash script: {flash_script}")
    print(f"  ELF: {elf_path}")

    try:
        dbg.cmm(f'"{flash_script}"', timeout=120)
        print(f"  Flash script executed")
    except Exception as e:
        print(f"  [WARN] cmm() exception: {e}")
        dbg.cmd(f'CD.DO "{flash_script}"')
        time.sleep(15)

    print(f"\n  Verifying symbols:")
    found = 0
    for name in ["core_main", "nx_start", "core0_main", "rtfw_init"]:
        addr = sym_addr(dbg, name)
        if addr is not None:
            print(f"    {name:<40s} @ 0x{addr:08X}")
            found += 1
    print(f"  Found {found} key symbols")


def phase3_breakpoints_and_run(dbg, cfg):
    banner("Phase 3: Set Breakpoints & Run")

    cmd(dbg, "Break.Delete /ALL")

    breakpoints = ["core_main", "core0_main", "nx_start"]
    for bp_name in breakpoints:
        addr = sym_addr(dbg, bp_name)
        if addr is not None:
            cmd(dbg, f"Break.Set {bp_name}")
        else:
            print(f"    {bp_name}: symbol not found, skipping")

    print("\n  Go (run)...")
    cmd(dbg, "Go")
    time.sleep(3)

    print("  Break (halt)...")
    dbg.break_()
    time.sleep(0.5)

    try:
        pc = dbg.register.read_by_name("PC").value
        func = pc_to_func(dbg, pc)
        print(f"  PC = 0x{pc:08X} -> {func}")
    except Exception as e:
        print(f"  State: {e}")


def phase4_inspect_state(dbg):
    banner("Phase 4: Inspect Runtime State")

    print("\n  [4a] Core registers:")
    for rname in ["PC", "SP", "A0", "A1", "D0", "D1", "D2", "D3"]:
        try:
            reg = dbg.register.read(rname)
            val = reg.value
            if isinstance(val, int):
                print(f"    {reg.name:<8s} = 0x{val:08X}")
            else:
                print(f"    {reg.name:<8s} = {val}")
        except Exception as e:
            print(f"    {rname:<8s} = [error: {e}]")

    print("\n  [4b] Memory (CPU0 DSPR):")
    try:
        addr = dbg.address.from_string("D:0xD0000000")
        data = dbg.memory.read(addr, length=64)
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset+16]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            print(f"      +{offset:04X}: {hex_str}")
    except Exception as e:
        print(f"      [error: {e}]")


def phase5_step(dbg):
    banner("Phase 5: Step Execution")
    for i in range(5):
        print(f"\n  --- Step {i+1} ---")
        try:
            if dbg.fnc.state_run():
                dbg.break_()
                time.sleep(0.3)
            dbg.cmd("Step")
            pc = dbg.register.read_by_name("PC").value
            func = pc_to_func(dbg, pc)
            print(f"    PC = 0x{pc:08X} -> {func}")
        except Exception as e:
            print(f"    [error: {e}]")
            break


def main():
    cfg = load_config()

    print("=" * 60)
    print("  DebugForge: TC397 Automated Debug Workflow")
    print("  Target: Infineon AURIX TC397 (TriCore)")
    print("=" * 60)

    try:
        dbg = phase1_connect(cfg)
        phase2_flash(dbg, cfg)
        phase3_breakpoints_and_run(dbg, cfg)
        phase4_inspect_state(dbg)
        phase5_step(dbg)

        banner("Done")
        cmd(dbg, "Break.Delete /ALL")
        print("  All breakpoints cleared")

    except ConnectionError as e:
        print(f"\n[FATAL] Connection failed: {e}")
        print("Check:")
        print("  1. Trace32 PowerView is running")
        print("  2. config.t32 has RCL=NETTCP PORT=20000")
        print("  3. Target board connected via JTAG")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
