#!/usr/bin/env python3
"""
Example: Remote debug workflow via WinRM + PYRCL

Demonstrates:
1. WinRM upload ELF + CMM to remote Windows
2. WinRM start Trace32
3. PYRCL connect and execute debug commands

Usage:
  1. Copy debugforge.toml.example to debugforge.toml
  2. Fill in your remote connection details
  3. Run: python examples/remote_debug.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from debugforge.config import load_config


def run_winrm_cmd(session, cmd: str, label: str = ""):
    """Execute a PowerShell command and print results."""
    if label:
        print(f"\n{label}")

    r = session.run_ps(cmd)
    out = r.std_out.decode('utf-8', errors='replace').strip()
    err = r.std_err.decode('utf-8', errors='replace').strip()

    if out:
        print(f"  stdout: {out}")
    if err and "CLIXML" not in err:
        print(f"  stderr: {err[:500]}")
    print(f"  exit: {r.status_code}")

    return r.status_code == 0


def main():
    import winrm

    cfg = load_config()
    remote = cfg.remote

    if not remote.host:
        print("Error: remote.host not configured in debugforge.toml")
        sys.exit(1)

    elf_path = cfg.elf
    flash_script = cfg.scripts.get("flash", "")

    if not elf_path or not os.path.exists(elf_path):
        print(f"Error: ELF file not found: {elf_path}")
        sys.exit(1)

    print("=" * 60)
    print("DebugForge: Remote Debug via WinRM + PYRCL")
    print("=" * 60)
    print(f"  Host: {remote.host}")
    print(f"  WinRM: {remote.winrm_url}")
    print(f"  Staging: {remote.staging_dir}")

    # Connect WinRM
    print(f"\nConnecting WinRM: {remote.winrm_url}")
    session = winrm.Session(
        remote.winrm_url,
        auth=(remote.winrm_user, remote.winrm_password),
        transport=remote.winrm_transport,
    )

    # 1. Create remote directory
    run_winrm_cmd(
        session,
        f'New-Item -ItemType Directory -Path "{remote.staging_dir}" -Force | Out-Null; Write-Output "Directory ready"',
        "Create remote directory",
    )

    # 2. Start Trace32
    t32_cmd = r'''
$t32 = "C:\T32\bin\windows64\t32mtc.exe"
$config = "C:\T32\config.t32"
$proc = Get-Process t32mtc -ErrorAction SilentlyContinue
if ($proc) {
    Write-Output "Trace32 already running (PID: $($proc.Id))"
} else {
    Start-Process -FilePath $t32 -ArgumentList "-c", $config
    Start-Sleep -Seconds 5
    Write-Output "Trace32 started"
}
'''
    run_winrm_cmd(session, t32_cmd, "Check/Start Trace32")

    # 3. Verify Trace32 RCL port
    run_winrm_cmd(
        session,
        f'Test-NetConnection -ComputerName {remote.host} -Port {cfg.port} -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded',
        "Verify Trace32 port",
    )

    print(f"\nTrace32 ready at {remote.host}:{cfg.port}")

    # 4. Optional: connect via PYRCL
    if '--pyrcl' in sys.argv:
        print(f"\nConnecting via PYRCL...")
        from lauterbach.trace32.rcl import connect
        dbg = connect(node=remote.host, port=str(cfg.port), protocol=cfg.protocol)
        print(f"Connected! Version: {dbg.fnc.version_software()}")

        if flash_script:
            remote_cmm = f"{remote.staging_dir}\\{os.path.basename(flash_script)}"
            print(f"Executing CMM: {remote_cmm}")
            dbg.cmd(f'DO "{remote_cmm}"')

        for translate in remote.source_translates:
            src = translate.get("from", "")
            dst = translate.get("to", "")
            if src and dst:
                dbg.cmd(f'SYmbol.SourcePATH.Translate "{src}" "{dst}"')

        print("Done!")


if __name__ == "__main__":
    main()
