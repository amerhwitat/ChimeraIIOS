#!/usr/bin/env python3
"""Safe DOSBox/DOSBox-X bridge for ChimeraIIOS and OctavianOS.

DOS binaries execute in an emulated guest PC. By default, mounted host folders
are read-only; CHIMERA_DOS_WRITABLE=1 opts into writes to the selected app folder.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

UNSAFE = set('"\r\n&|<>^%!')

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

def emulator_commands(exe: str, host_dir: Path, program: str, args: list[str]) -> int:
    if not safe_dos_arg(str(host_dir)) or not safe_dos_arg(program) or not all(safe_dos_arg(a) for a in args):
        return fail("DOS path or argument contains quotes, control characters, or command metacharacters", 2)
    writable = os.environ.get("CHIMERA_DOS_WRITABLE") == "1"
    mount = 'mount c "' + str(host_dir) + '"' + ("" if writable else " -ro")
    rendered = [('"'+arg+'"') if any(ch.isspace() for ch in arg) else arg for arg in args]
    command = ('"'+program+'"') + ((" " + " ".join(rendered)) if rendered else "")
    cmd = [exe, "-c", mount, "-c", "c:", "-c", command, "-c", "exit"]
    try:
        return subprocess.run(cmd, check=False).returncode
    except OSError as exc:
        return fail(f"could not start emulator: {exc}")

def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: chimera-dos-adapter.py --run DOSFILE [ARG...] | --command DOSCOMMAND [ARG...]")
        print("DOS guest folders are read-only by default; CHIMERA_DOS_WRITABLE=1 opts into writes.")
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
        return emulator_commands(exe, program.parent, program.name, items[1:])
    command = items[0].lower()
    if not re.fullmatch(r"[a-z0-9_-]+(?:\.(?:com|exe|bat))?", command):
        return fail("invalid DOS command name", 2)
    bin_dir = Path(os.environ.get("CHIMERA_DOS_BIN", "/usr/share/chimera/dos/bin")).resolve()
    if not bin_dir.is_dir():
        return fail(f"DOS command payload directory is absent: {bin_dir}; install a licensed DOS command payload package")
    base = command[:-4] if command.endswith((".com", ".exe", ".bat")) else command
    executable = next((bin_dir / (base + suffix) for suffix in (".com", ".exe", ".bat") if (bin_dir / (base + suffix)).is_file()), None)
    if executable is None:
        return fail(f"DOS command payload not installed: {bin_dir / (base + '.com/.exe/.bat')}", 127)
    return emulator_commands(exe, bin_dir, executable.name, items[1:])

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
