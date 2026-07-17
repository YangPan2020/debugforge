"""Memory access tools for TRACE32."""

from __future__ import annotations

from debugforge.server import mcp
from debugforge.state import state


@mcp.tool()
async def read_memory(
    address: str,
    length: int,
    width: int = 32,
    access: str = "",
) -> str:
    """Read memory from the target at a given address.

    Args:
        address: Memory address as hex string (e.g., "0x80000000") or symbol name (e.g., "main")
        length: Number of bytes to read
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)
        access: Access class prefix (e.g., "D:" for data, "P:" for program). Empty = default.

    Returns:
        Hex dump of memory contents
    """
    dbg = state.require_connection()
    try:
        addr_str = f"{access}{address}" if access else address
        addr = dbg.address.from_string(addr_str)
        data = dbg.memory.read(addr, length=length, width=width // 8 if width > 8 else None)

        hex_lines = []
        bytes_per_line = 16
        # Parse the numeric address for display, stripping any access class prefix
        try:
            addr_val = int(address.lstrip("DPSBCadpsbc:"), 16)
        except ValueError:
            addr_val = 0
        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            display_addr = addr_val + offset if addr_val else offset
            hex_lines.append(f"0x{display_addr:08X}: {hex_part:<48s} |{ascii_part}|")

        return "\n".join(hex_lines) if hex_lines else "No data read"
    except ConnectionError:
        raise
    except Exception as e:
        return f"Error reading memory at {address}: {e}"


@mcp.tool()
async def write_memory(
    address: str,
    data: str,
    width: int = 32,
    access: str = "",
) -> str:
    """Write data to target memory at a given address.

    Args:
        address: Memory address as hex string (e.g., "0x80000000") or symbol name
        data: Hex string of bytes to write (e.g., "DEADBEEF" for 4 bytes)
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)
        access: Access class prefix (e.g., "D:" for data). Empty = default.

    Returns:
        Confirmation with number of bytes written
    """
    dbg = state.require_connection()
    try:
        addr_str = f"{access}{address}" if access else address
        addr = dbg.address.from_string(addr_str)
        byte_data = bytes.fromhex(data)
        dbg.memory.write(addr, byte_data, width=width // 8 if width > 8 else None)
        return f"Wrote {len(byte_data)} bytes to {address}"
    except ConnectionError:
        raise
    except ValueError as e:
        return f"Invalid hex data '{data}': {e}"
    except Exception as e:
        return f"Error writing memory at {address}: {e}"


@mcp.tool()
async def read_memory_cached(
    address: str,
    length: int,
    width: int = 32,
) -> str:
    """Read memory using cache-aware access (D: prefix).

    Shows data as the CPU sees it through its data cache, not the stale
    value on the bus. Essential for debugging code that modifies cached
    memory (e.g., shared variables in LMU on TC39x).

    Args:
        address: Memory address as hex string (e.g., "0x80000000")
        length: Number of bytes to read
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)

    Returns:
        Hex dump of cached memory contents
    """
    return await read_memory(address, length, width, access="D:")


@mcp.tool()
async def read_memory_physical(
    address: str,
    length: int,
    width: int = 32,
) -> str:
    """Read physical memory bypassing the CPU cache.

    Reads the actual value on the memory bus, which may differ from what
    the CPU sees if the data cache has not been flushed.

    Args:
        address: Memory address as hex string (e.g., "0x80000000")
        length: Number of bytes to read
        width: Access width in bits — 8, 16, 32, or 64 (default: 32)

    Returns:
        Hex dump of physical memory contents
    """
    return await read_memory(address, length, width, access="")


@mcp.tool()
async def list_access_classes() -> str:
    """List all available memory access classes for TRACE32.

    Shows the different access class prefixes that can be used to read
    memory through different paths (cache, bus, peripheral, etc.).

    Returns:
        Table of access classes with descriptions
    """
    rows = [
        ("(none)", "Default access — bus-level (may show stale cache data)"),
        ("D:", "Data access — shows CPU's view through data cache"),
        ("P:", "Program access — instruction memory space"),
        ("DC:", "Data cache direct — read data cache contents"),
        ("IC:", "Instruction cache direct — read I-cache contents"),
        ("PER:", "Peripheral access — SFR/peripheral registers"),
        ("DUALPORT:", "Dual-port RAM access (if supported)"),
    ]
    lines = ["Memory Access Classes:", ""]
    for prefix, desc in rows:
        lines.append(f"  {prefix:12s}  {desc}")
    return "\n".join(lines)
