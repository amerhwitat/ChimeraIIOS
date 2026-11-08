#!/usr/bin/env python3
"""Launch one installed X11 desktop session from its XDG xsessions entry."""
from __future__ import annotations
import configparser
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

SESSION_DIRS = tuple(Path(p) for p in os.environ.get("CHIMERA_XSESSION_DIRS", "/usr/local/share/xsessions:/usr/share/xsessions").split(os.pathsep) if p)
FIELD_CODES = re.compile(r"%(?:[fFuUdDnNickvm]|%)")

def entries():
    found = {}
    for directory in SESSION_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.desktop")):
            found.setdefault(path.stem, path)
    return found

def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9_.+-]{1,80}", sys.argv[1]):
        print("usage: chimera-xsession SESSION_ID", file=sys.stderr)
        return 2
    session_id = sys.argv[1]
    path = entries().get(session_id)
    if path is None:
        print(f"X11 session not installed: {session_id}", file=sys.stderr)
        return 127
    desktop = configparser.ConfigParser(interpolation=None, strict=False)
    desktop.optionxform = str
    try:
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
            test = try_exec if os.path.isabs(try_exec) else shutil.which(try_exec)
            if not test or not os.access(test, os.X_OK):
                raise FileNotFoundError(f"session TryExec is unavailable: {try_exec}")
        argv[0] = resolved
        name = section.get("Name", session_id)
    except (OSError, ValueError, KeyError, configparser.Error) as exc:
        print(f"chimera-xsession: {path}: {exc}", file=sys.stderr)
        return 126
    os.environ.update({
        "DESKTOP_SESSION": session_id,
        "GDMSESSION": session_id,
        "XDG_SESSION_TYPE": "x11",
        "XDG_CURRENT_DESKTOP": os.environ.get("XDG_CURRENT_DESKTOP", name),
    })
    print(f"[Aurora X11] launching {name} ({session_id})", flush=True)
    os.execvpe(argv[0], argv, os.environ)
    return 126

if __name__ == "__main__":
    raise SystemExit(main())
