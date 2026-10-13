#!/usr/bin/env python3
"""Safe DOSBox/DOSBox-X bridge for ChimeraIIOS and OctavianOS.

This launches DOS binaries in an emulated PC. It never grants guest code direct
access to the host's physical memory, devices, or kernel address space.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path

UNSAFE = set('"\r\n&|<>^')

def fail(message: str, code: int = 126) -> int:
    print(f"chimera-dos: {message}", file=sys.stderr)
    return code

def provider() -> str | None:
    for name in (os.environ.get("CHIMERA_DOS_EMULATOR", ""), "dosbox-x", "dosbox"):
        if name and (path := shutil.which(name)):
            return path
    return None

def safe_dos_arg(value: str) -> bool:
    return not any(ch in UNSAFE or ord(ch) < 32 for ch in value)

def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: chimera-dos-adapter.py --run DOSFILE [ARG...] | --command DOSCOMMAND [ARG...]")
        return 0 if argv else 2
    mode, *items = argv
    if mode not in ("--run", "--command") or not items:
        return fail("invalid mode or missing program", 2)
    exe = provider()
    if not exe:
        return fail("DOSBox-X/DOSBox is not installed; install a provider before launching DOS software")
    if mode == "--run":
        program = Path(items[0]).expanduser().resolve()
        if not program.is_file():
            return fail(f"DOS program not found: {program}", 127)
        if program.suffix.lower() not in (".com", ".exe", ".bat"):
            return fail("only DOS .COM, .EXE, and .BAT launch targets are accepted")
        # DOSBox-X and DOSBox accept a DOS executable as a launch target. The
        # emulator owns the guest CPU, memory map, BIOS and device model.
        try:
            return subprocess.run([exe, str(program), *items[1:]], check=False).returncode
        except OSError as exc:
            return fail(f"could not start emulator: {exc}")
    command = items[0].lower()
    bin_dir = Path(os.environ.get("CHIMERA_DOS_BIN", "/usr/share/chimera/dos/bin")).resolve()
    if not bin_dir.is_dir():
        return fail(f"DOS command payload directory is absent: {bin_dir}; install a licensed DOS command payload package")
    base = command[:-4] if command.endswith((".com", ".exe", ".bat")) else command
    executable = next((bin_dir / (base + suffix) for suffix in (".com", ".exe", ".bat") if (bin_dir / (base + suffix)).is_file()), None)
    if executable is None:
        # DOSBox's internal commands are not host commands. Never claim an
        # external DOS command is available merely because it is in a catalog.
        return fail(f"DOS command payload not installed: {bin_dir / (base + '.com/.exe/.bat')}", 127)
    dos_args = items[1:]
    if not all(safe_dos_arg(arg) for arg in [str(bin_dir), executable.name, *dos_args]):
        return fail("DOS command contains quotes, control characters, or shell metacharacters; refusing ambiguous DOS command syntax", 2)
    host_dir = str(bin_dir)
    rendered_args = [('"'+arg+'"') if any(ch.isspace() for ch in arg) else arg for arg in dos_args]
    commands = ["mount c " + '"' + host_dir + '"', "c:", executable.name + ((" " + " ".join(rendered_args)) if rendered_args else ""), "exit"]
    try:
        argv = [exe]
        for command_line in commands:
            argv.extend(["-c", command_line])
        return subprocess.run(argv, check=False).returncode
    except OSError as exc:
        return fail(f"could not start emulator: {exc}")

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
