#!/usr/bin/env python3
"""Build a Chimera command catalog from the current host plus standards metadata.

The catalog records availability rather than pretending that Linux/UNIX flavors
share identical options. It discovers PATH executables and shell builtins when
bash/zsh are installed, and records the source family separately.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess
from pathlib import Path

SHELLS = ["sh", "bash", "zsh", "dash", "ksh", "ash", "csh", "tcsh", "fish"]


def command_names_from_path():
    names = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        try:
            for entry in os.listdir(directory):
                full = os.path.join(directory, entry)
                if os.path.isfile(full) and os.access(full, os.X_OK): names.add(entry)
        except OSError:
            pass
    return names


def builtins(shell):
    if not shutil.which(shell): return []
    commands = {"sh": [shell, "-c", "command -V"], "bash": [shell, "-c", "compgen -b"], "zsh": [shell, "-fc", "print -l ${(k)builtins}"], "dash": [shell, "-c", "command -V"]}
    cmd = commands.get(shell)
    if not cmd: return []
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
        return sorted({line.split()[0] for line in p.stdout.splitlines() if line.strip()})
    except (OSError, subprocess.SubprocessError): return []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, default=Path("tools/shell/chimera_command_registry.json")); args = ap.parse_args()
    entries = {}
    for name in command_names_from_path():
        entries.setdefault(name, {"name":name, "availability":["PATH"], "kind":"external-or-multicall"})
    for shell in SHELLS:
        for name in builtins(shell):
            entries.setdefault(name, {"name":name, "availability":[], "kind":"shell-builtin"})
            entries[name]["availability"].append(shell)
    doc = {
        "schema":"chimera-ii-command-registry", "schema_version":1,
        "generated":True,
        "host": {"platform": os.uname().sysname if hasattr(os, "uname") else os.name},
        "resolution_order":["alias","function","builtin","reserved-word","PATH executable"],
        "sources":"tools/shell/chimera_command_sources.json",
        "commands": sorted(entries.values(), key=lambda x:x["name"])
    }
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")
    print(f"generated {args.output}: {len(doc['commands'])} command names")

if __name__ == "__main__": main()
