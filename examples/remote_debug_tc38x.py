#!/usr/bin/env python3
"""
Example: Remote debug TC38x via network drive + PYRCL

Demonstrates direct file access via mapped network drive (Z:) and
safe Trace32 shutdown via QUIT command.

Safety measures:
- Must execute dbg.cmd('QUIT') before exit to cleanly close Trace32
- Force-killing the process can cause hardware errors
- All exit paths (normal/exception/signal) execute QUIT

Usage:
  1. Copy debugforge.toml.example to debugforge.toml
  2. Fill in your connection details
  3. Run: python examples/remote_debug_tc38x.py
"""

import os
import sys
import signal
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lauterbach.trace32.rcl import connect
from debugforge.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

dbg_connection = None


def safe_quit_trace32(dbg):
    """Safely close Trace32 via QUIT command."""
    if not dbg:
        return
    try:
        logging.info('[T32] Sending QUIT command to safely close Trace32 PowerView...')
        dbg.cmm('QUIT')
        logging.info('Trace32 closed safely')
        time.sleep(2)
    except Exception as e:
        logging.error(f'Error closing Trace32: {e}')


def signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    logging.warning(f'Received signal {sig_name}, shutting down Trace32...')
    global dbg_connection
    if dbg_connection:
        safe_quit_trace32(dbg_connection)
    sys.exit(128 + signum)


def main():
    global dbg_connection

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    cfg = load_config()
    remote = cfg.remote
    host = remote.host or cfg.node
    port = str(cfg.port)

    logging.info("=" * 70)
    logging.info("Remote Debug TC38x")
    logging.info(f"  Host: {host}:{port}")
    logging.info("=" * 70)

    dbg = None
    try:
        logging.info(f"[1/4] Connecting Trace32 ({host}:{port})...")
        dbg = connect(node=host, port=port, protocol='TCP', timeout=120)
        dbg_connection = dbg
        logging.info("Connected")

        logging.info("[2/4] Verifying connection...")
        version = dbg.fnc.version_software()
        logging.info(f"Trace32 version: {version}")

        cmm_path = cfg.scripts.get("flash", "")
        elf_path = cfg.elf

        if cmm_path:
            logging.info(f"[3/4] Executing CMM: {cmm_path}")
            logging.info(f"      Loading ELF: {elf_path}")
            result = dbg.cmm(cmm_path)
            logging.info(f"CMM execution complete")
            time.sleep(3)

        logging.info("[4/4] Verifying ELF load...")
        try:
            pc_value = dbg.register.read("PC")
            logging.info(f"ELF loaded, PC: 0x{pc_value.value:08X}")
        except Exception as e:
            logging.warning(f"Cannot read PC: {e}")

        logging.info("Debug session complete, shutting down...")

    except ConnectionError as e:
        logging.error(f"Connection failed: {e}")
        logging.error("Check: 1) Trace32 running  2) RCL=NETTCP PORT=20000  3) Firewall")
        return 1
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        safe_quit_trace32(dbg)
        dbg_connection = None

    return 0


if __name__ == "__main__":
    sys.exit(main())
