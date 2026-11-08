#!/usr/bin/env python3
"""Launch a real installed XDG X11 or Wayland desktop session.

This dispatcher does not provide a display server. X11 sessions use the installed
X.Org server through chimera-xserver-session; Wayland sessions launch their
installed compositor/session entry. Missing providers fail closed.
"""
from __future__ import annotations
import configparser
import os
import re
import shlex
import shutil
import stat
import sys
from pathlib import Path

FIELD_CODES = re.compile(r"%(?:[fFuUdDnNickvm]|%)")
SESSION_ID = re.compile(r"^[A-Za-z0-9_.+-]{1,80}$")

def session_dirs(kind: str) -> tuple[Path, ...]:
    env_name = "CHIMERA_WAYLAND_SESSION_DIRS" if kind == "wayland" else "CHIMERA_XSESSION_DIRS"
    default = ("/usr/local/share/wayland-sessions:/usr/share/wayland-sessions"
               if kind == "wayland" else
               "/usr/local/share/xsessions:/usr/share/xsessions")
    return tuple(Path(p) for p in os.environ.get(env_name, default).split(os.pathsep) if p)

def entries(kind: str) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for directory in session_dirs(kind):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.desktop")):
            found.setdefault(path.stem, path)
    return found

def load_session(path: Path, session_id: str) -> tuple[list[str], str]:
    desktop = configparser.ConfigParser(interpolation=None, strict=False)
    desktop.optionxform = str
    with path.open(encoding="utf-8") as stream:
        desktop.read_file(stream)
    section = desktop["Desktop Entry"]
    if section.get("Type", "Application") != "Application":
        raise ValueError("desktop entry is not an Application")
    if section.get("Hidden", "false").lower() == "true" or section.get("NoDisplay", "false").lower() == "true":
        raise ValueError("desktop session is hidden")
    command = FIELD_CODES.sub("", section.get("Exec", "")).strip()
    argv = shlex.split(command)
    if not argv:
        raise ValueError("session Exec is empty")
    executable = argv[0]
    resolved = executable if os.path.isabs(executable) else shutil.which(executable)
    if not resolved or not os.path.isfile(resolved) or not os.access(resolved, os.X_OK):
        raise FileNotFoundError(f"session executable is not installed: {executable}")
    try_exec = section.get("TryExec", "").strip()
    if try_exec:
        try_argv = shlex.split(try_exec)
        test_exec = try_argv[0] if try_argv else ""
        test = test_exec if os.path.isabs(test_exec) else shutil.which(test_exec)
        if not test or not os.path.isfile(test) or not os.access(test, os.X_OK):
            raise FileNotFoundError(f"session TryExec is unavailable: {test_exec}")
    argv[0] = resolved
    return argv, section.get("Name", session_id)

def list_sessions(kind: str) -> int:
    found = entries(kind)
    for session_id, path in sorted(found.items()):
        try:
            _, name = load_session(path, session_id)
            status = "available"
        except (OSError, ValueError, KeyError, configparser.Error):
            name, status = session_id, "provider-missing"
        print(f"{kind}\t{session_id}\t{name}\t{status}")
    return 0 if found else 1

def main() -> int:
    args = sys.argv[1:]
    kind = "x11"
    if len(args) >= 2 and args[0] == "--type":
        kind, args = args[1], args[2:]
    if kind not in ("x11", "wayland"):
        print("chimera-xsession: --type must be x11 or wayland", file=sys.stderr)
        return 2
    if args in (["--help"], ["-h"], ["help"]):
        print("Usage: chimera-xsession [--type x11|wayland] SESSION_ID")
        print("       chimera-xsession [--type x11|wayland] --list")
        return 0
    if args == ["--list"]:
        return list_sessions(kind)
    if len(args) != 1 or not SESSION_ID.fullmatch(args[0]):
        print("usage: chimera-xsession [--type x11|wayland] SESSION_ID", file=sys.stderr)
        return 2
    session_id = args[0]
    path = entries(kind).get(session_id)
    if path is None:
        print(f"{kind} session not installed: {session_id}", file=sys.stderr)
        return 127
    try:
        argv, name = load_session(path, session_id)
        if kind == "wayland":
            if os.geteuid() == 0:
                raise PermissionError("refusing to launch a Wayland user session as root")
            runtime = os.environ.get("XDG_RUNTIME_DIR", "")
            runtime_path = Path(runtime) if runtime else None
            if runtime_path is None or not runtime_path.is_dir():
                raise PermissionError("XDG_RUNTIME_DIR is missing; log in through a user session manager first")
            info = runtime_path.stat()
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise PermissionError("XDG_RUNTIME_DIR must be owned by the user and have mode 0700")
    except (OSError, ValueError, KeyError, configparser.Error) as exc:
        print(f"chimera-xsession: {path}: {exc}", file=sys.stderr)
        return 126
    os.environ.update({
        "DESKTOP_SESSION": session_id,
        "GDMSESSION": session_id,
        "XDG_SESSION_TYPE": kind,
        "XDG_CURRENT_DESKTOP": os.environ.get("XDG_CURRENT_DESKTOP", name),
    })
    print(f"[Chimera {kind.upper()}] launching {name} ({session_id})", flush=True)
    os.execvpe(argv[0], argv, os.environ)
    return 126

if __name__ == "__main__":
    raise SystemExit(main())
