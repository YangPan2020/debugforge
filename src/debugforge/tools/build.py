"""Build integration and binary analysis tools."""

from __future__ import annotations

import asyncio
import shutil

from debugforge.server import mcp
from debugforge.state import config


@mcp.tool()
async def build_project() -> str:
    """Build the project using the configured build command.

    Executes the build command defined in debugforge.toml [build] section.
    Returns the build output including any errors or warnings.

    Returns:
        Build output (stdout + stderr) with success/failure status
    """
    if not config.build_command:
        return "Error: No build command configured. Set [build] command in debugforge.toml"

    cwd = config.build_working_dir or config.config_dir or None
    try:
        proc = await asyncio.create_subprocess_shell(
            config.build_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode(errors="replace")
        if proc.returncode == 0:
            return f"Build successful.\n{output}" if output else "Build successful."
        else:
            return f"Build FAILED (exit code {proc.returncode}).\n{output}"
    except Exception as e:
        return f"Build error: {e}"


@mcp.tool()
async def clean_project() -> str:
    """Clean the project build artifacts using the configured clean command.

    Returns:
        Clean output with success/failure status
    """
    if not config.clean_command:
        return "Error: No clean command configured. Set [build] clean_command in debugforge.toml"

    cwd = config.build_working_dir or config.config_dir or None
    try:
        proc = await asyncio.create_subprocess_shell(
            config.clean_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode(errors="replace")
        if proc.returncode == 0:
            return f"Clean successful.\n{output}" if output else "Clean successful."
        else:
            return f"Clean FAILED (exit code {proc.returncode}).\n{output}"
    except Exception as e:
        return f"Clean error: {e}"


@mcp.tool()
async def disassemble(symbol: str = "", address: str = "", lines: int = 50) -> str:
    """Disassemble a function or address range from the project ELF file.

    Uses the configured objdump tool to produce disassembly output.

    Args:
        symbol: Function name to disassemble (e.g., "main", "ISR_Handler")
        address: Start address in hex (e.g., "0x80001000"). Used if symbol is empty.
        lines: Maximum number of lines to return (default: 50)

    Returns:
        Disassembly listing
    """
    if not config.elf:
        return "Error: No ELF file configured. Set [project] elf in debugforge.toml"

    objdump = config.objdump
    if not objdump:
        return "Error: No objdump tool configured. Set [toolchain] objdump in debugforge.toml"

    if config.compiler_path:
        full_path = shutil.which(objdump, path=config.compiler_path)
        if full_path:
            objdump = full_path

    if symbol:
        cmd = f'{objdump} -d -C --no-show-raw-insn {config.elf} | grep -A {lines} "^[0-9a-f]* <{symbol}>:"'
    elif address:
        addr_int = int(address, 16) if address.startswith("0x") else int(address, 16)
        cmd = f"{objdump} -d -C --start-address=0x{addr_int:x} --stop-address=0x{addr_int + lines * 4:x} {config.elf}"
    else:
        return "Error: Provide either 'symbol' or 'address' parameter"

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode(errors="replace").strip()
        if not output:
            err = stderr.decode(errors="replace").strip()
            if err:
                return f"Disassembly error: {err}"
            return f"No disassembly found for {'symbol: ' + symbol if symbol else 'address: ' + address}"
        return output
    except Exception as e:
        return f"Disassembly error: {e}"


@mcp.tool()
async def analyze_map(section: str = "", symbol: str = "") -> str:
    """Analyze the project MAP file to understand memory layout.

    Shows memory section sizes, symbol addresses, or searches for a specific symbol.

    Args:
        section: Filter by section name (e.g., ".text", ".bss", ".data"). Empty for overview.
        symbol: Search for a specific symbol in the MAP file.

    Returns:
        MAP file analysis (memory layout, section sizes, or symbol info)
    """
    if not config.map:
        return "Error: No MAP file configured. Set [project] map in debugforge.toml"

    try:
        with open(config.map, "r", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        return f"Error: MAP file not found: {config.map}"
    except Exception as e:
        return f"Error reading MAP file: {e}"

    if symbol:
        matches = [line for line in content.splitlines() if symbol in line]
        if matches:
            return f"Symbol '{symbol}' in MAP file:\n" + "\n".join(matches[:30])
        return f"Symbol '{symbol}' not found in MAP file"

    if section:
        matches = [line for line in content.splitlines() if section in line]
        if matches:
            return f"Section '{section}' in MAP file:\n" + "\n".join(matches[:50])
        return f"Section '{section}' not found in MAP file"

    # Overview: return first 100 lines (usually contains memory summary)
    lines_list = content.splitlines()
    if len(lines_list) > 100:
        return "\n".join(lines_list[:100]) + f"\n\n... ({len(lines_list)} total lines, use section/symbol filter for details)"
    return content


@mcp.tool()
async def analyze_elf(detail: str = "headers") -> str:
    """Analyze the project ELF file structure.

    Uses readelf to inspect ELF headers, sections, or symbols.

    Args:
        detail: What to show — "headers", "sections", "symbols", or "size" (default: headers)

    Returns:
        ELF analysis output
    """
    if not config.elf:
        return "Error: No ELF file configured. Set [project] elf in debugforge.toml"

    readelf = config.readelf
    if not readelf:
        return "Error: No readelf tool configured. Set [toolchain] readelf in debugforge.toml"

    if config.compiler_path:
        full_path = shutil.which(readelf, path=config.compiler_path)
        if full_path:
            readelf = full_path

    flag_map = {
        "headers": "-h",
        "sections": "-S",
        "symbols": "-s",
        "size": "-l",
    }
    flag = flag_map.get(detail, "-h")

    try:
        proc = await asyncio.create_subprocess_exec(
            readelf, flag, config.elf,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode(errors="replace").strip()
        if not output:
            err = stderr.decode(errors="replace").strip()
            return f"ELF analysis error: {err}" if err else "No output from readelf"
        return output
    except FileNotFoundError:
        return f"Error: readelf tool not found: {readelf}. Check [toolchain] readelf in debugforge.toml"
    except Exception as e:
        return f"ELF analysis error: {e}"
