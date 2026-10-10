#!/usr/bin/env python3
"""Chimera II Hosted Edition bridge for 64-bit Windows, Linux, Unix and macOS.

This is a portable user-mode host bridge, not a virtual machine or a replacement
kernel. It provides host/ISA discovery, command aliases, safe built-in file
commands, desktop open integration, and explicit pass-through to host processes.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISA_DB = ROOT / "isa" / "isa_database.json"
ALIASES = {
    "windows": {"ls": "dir", "cat": "type", "cp": "copy", "mv": "move", "rm": "del", "pwd": "pwd"},
    "linux": {"dir": "ls", "type": "cat", "copy": "cp", "move": "mv", "del": "rm", "cls": "clear"},
    "unix": {"dir": "ls", "type": "cat", "copy": "cp", "move": "mv", "del": "rm", "cls": "clear"},
    "macos": {"dir": "ls", "type": "cat", "copy": "cp", "move": "mv", "del": "rm", "cls": "clear"},
}
BUILTINS = {"pwd", "ls", "dir", "echo", "cat", "type", "mkdir", "cp", "copy", "mv", "move", "rm", "del", "whoami", "uname", "env", "set", "clear", "cls"}

def host_family():
    system = platform.system().lower()
    if system == "windows": return "windows"
    if system == "darwin": return "macos"
    if system == "linux":
        if "microsoft" in platform.release().lower() or os.environ.get("WSL_DISTRO_NAME"): return "linux-wsl"
        return "linux"
    if system in {"freebsd", "openbsd", "netbsd", "dragonfly"}: return "unix"
    return "unix" if system else "unknown"

def host_isa():
    machine = platform.machine().lower()
    return {
        "amd64": "x86-64", "x86_64": "x86-64", "x64": "x86-64",
        "i386": "x86-32", "i686": "x86-32", "x86": "x86-32",
        "arm64": "aarch64", "aarch64": "aarch64", "armv8l": "aarch64",
        "armv7l": "arm32", "riscv64": "riscv64", "riscv32": "riscv32",
    }.get(machine, machine or "unknown")

def load_isa_db():
    for path in (ISA_DB, Path(sys.prefix) / "share/chimera/isa/isa_database.json",
                 Path("/usr/share/chimera/isa/isa_database.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("architectures"), list): return data
        except (OSError, json.JSONDecodeError):
            pass
    return {"architectures": [], "instructions": [], "execution_model": {}}

def info():
    fam = host_family()
    return {
        "product": "Chimera II Hosted Edition",
        "runtime_kind": "hosted-user-mode-bridge",
        "host_os": platform.platform(),
        "host_family": fam,
        "host_kernel": platform.system(),
        "host_release": platform.release(),
        "host_isa": host_isa(),
        "pointer_bits": 64 if sys.maxsize > 2**32 else 32,
        "python": platform.python_version(),
        "hosted_edition_supported": fam in {"windows", "linux", "linux-wsl", "unix", "macos"} and sys.maxsize > 2**32,
        "desktop_open": "os.startfile" if os.name == "nt" else ("open" if fam == "macos" else "xdg-open"),
        "note": "Hosted mode extends the host through a user-space runtime; it does not boot Koronos or emulate a complete guest OS."
    }

def builtin(argv):
    if not argv: return 0
    cmd = argv[0].lower()
    args = argv[1:]
    try:
        if cmd in {"pwd"}:
            print(Path.cwd()); return 0
        if cmd in {"ls", "dir"}:
            target = Path(args[0]) if args else Path(".")
            for item in sorted(target.iterdir(), key=lambda p: p.name.casefold()):
                print(item.name + (os.sep if item.is_dir() else ""))
            return 0
        if cmd == "echo":
            print(" ".join(args)); return 0
        if cmd in {"cat", "type"}:
            if not args: print("usage: cat FILE...", file=sys.stderr); return 2
            for name in args:
                with open(name, "r", encoding="utf-8", errors="replace") as stream:
                    sys.stdout.write(stream.read())
            return 0
        if cmd == "mkdir":
            if not args: print("usage: mkdir DIRECTORY...", file=sys.stderr); return 2
            for name in args: Path(name).mkdir(parents=False, exist_ok=False)
            return 0
        if cmd in {"cp", "copy"}:
            if len(args) != 2: print("usage: cp SOURCE DEST", file=sys.stderr); return 2
            src, dst = map(Path, args)
            shutil.copy2(src, dst / src.name if dst.is_dir() else dst); return 0
        if cmd in {"mv", "move"}:
            if len(args) != 2: print("usage: mv SOURCE DEST", file=sys.stderr); return 2
            shutil.move(args[0], args[1]); return 0
        if cmd in {"rm", "del"}:
            if not args: print("usage: rm FILE...", file=sys.stderr); return 2
            for name in args:
                p = Path(name)
                if p.is_dir(): print(f"refusing to recursively remove directory: {p}", file=sys.stderr); return 2
                p.unlink()
            return 0
        if cmd == "whoami":
            print(os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"); return 0
        if cmd == "uname":
            if "-a" in args: print(platform.platform())
            else: print(platform.system())
            return 0
        if cmd in {"env", "set"}:
            for k, v in sorted(os.environ.items()): print(f"{k}={v}")
            return 0
        if cmd in {"clear", "cls"}:
            print("\n" * 60, end=""); return 0
    except (OSError, ValueError) as exc:
        print(f"chimera-hosted: {exc}", file=sys.stderr); return 1
    return None

def translate(command, mode):
    key = mode.lower()
    if key in {"darwin", "mac", "macos", "osx"}: key = "macos"
    if key in {"bsd", "posix"}: key = "unix"
    if key not in ALIASES: key = "linux"
    canonical = command.lower()
    return {"input": command, "mode": key, "canonical": ALIASES[key].get(canonical, canonical),
            "alias_applied": ALIASES[key].get(canonical, canonical) != canonical}

def open_path(name):
    path = str(Path(name).expanduser().resolve())
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif host_family() == "macos":
            subprocess.Popen(["open", path], close_fds=True)
        else:
            opener = shutil.which("xdg-open")
            if not opener: raise RuntimeError("xdg-open is unavailable on this host")
            subprocess.Popen([opener, path], close_fds=True)
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"chimera-hosted: cannot open {path}: {exc}", file=sys.stderr); return 1

def run_command(command, mode):
    if not command: return 2
    mapped = translate(command[0], mode)
    command = [mapped["canonical"], *command[1:]]
    result = builtin(command)
    if result is not None: return result
    executable = shutil.which(command[0])
    if not executable:
        print(f"chimera-hosted: command not found: {command[0]}", file=sys.stderr); return 127
    try: return subprocess.call([executable, *command[1:]], shell=False)
    except OSError as exc:
        print(f"chimera-hosted: cannot execute {command[0]}: {exc}", file=sys.stderr); return 126

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("info", help="report the host OS and physical ISA")
    sub.add_parser("desktop-info", help="report Aurora hosted-desktop bridge capabilities")
    ls = sub.add_parser("compat", help="list compatibility modes")
    ls.add_argument("operation", choices=("list",), default="list", nargs="?")
    tr = sub.add_parser("translate", help="translate a command alias for a compatibility mode")
    tr.add_argument("--mode", choices=("windows","linux","unix","macos","darwin","bsd"), default=host_family().replace("linux-wsl","linux"))
    tr.add_argument("command")
    run = sub.add_parser("run", help="run a safe built-in or host executable without shell interpolation")
    run.add_argument("--mode", choices=("windows","linux","unix","macos","darwin","bsd"), default=host_family().replace("linux-wsl","linux"))
    run.add_argument("command", nargs=argparse.REMAINDER)
    isa = sub.add_parser("isa", help="match the host ISA to inventoried Chimera candidates")
    isa.add_argument("--json", action="store_true")
    op = sub.add_parser("open", help="open a file or URL with the host desktop")
    op.add_argument("path")
    args = ap.parse_args(argv)
    if args.action == "info":
        print(json.dumps(info(), indent=2)); return 0
    if args.action == "desktop-info":
        data = info()
        data["desktop_bridge"] = {"available": data["hosted_edition_supported"],
            "operations": ["open host file/URL", "launch host process", "shared host filesystem"],
            "Aurora_integration": "bridge API available; full graphical desktop/compositor is a separate target"}
        print(json.dumps(data, indent=2)); return 0
    if args.action == "compat":
        print(json.dumps({"host": host_family(), "modes": {
            "windows": {"abi": "Win32/NT compatibility contracts", "execution": "native PE runner required for Windows binaries"},
            "linux": {"abi": "Linux/POSIX hosted user-space", "execution": "host executables and POSIX aliases"},
            "unix": {"abi": "POSIX/BSD hosted user-space", "execution": "host executables and POSIX aliases"},
            "macos": {"abi": "Darwin hosted user-space", "execution": "host executables and POSIX aliases"}},
            "limitations": ["not a syscall emulator", "not a Windows API implementation", "not a guest kernel"]}, indent=2)); return 0
    if args.action == "isa":
        db = load_isa_db()
        target = host_isa()
        rows = [row for row in db.get("architectures", []) if row and str(row[0]).lower() == target.lower()]
        data = {"host_isa": target, "host_architecture_candidate": rows[0] if rows else None,
            "inventory_match": bool(rows), "execution_policy": "host-native execution uses the host OS ABI; guest ISA execution requires a validated decoder/backend",
            "candidate_runtime": "tools/isa/chimera_isa_candidate.py",
            "warning": "ISA inventory match does not mean that a compiler backend or emulator exists."}
        print(json.dumps(data, indent=2)); return 0
    if args.action == "translate":
        print(json.dumps(translate(args.command,args.mode), indent=2)); return 0
    if args.action == "open": return open_path(args.path)
    if args.action == "run":
        command = list(args.command)
        if command and command[0] == "--": command = command[1:]
        return run_command(command,args.mode)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
