#!/usr/bin/env python3
"""Chimera II OS command catalog and safe command dispatcher.

This is a catalog/compatibility front-end, not a replacement for Bash.
Use:
  chimera commands
  chimera native
  chimera search <term>
  chimera help <command>
  chimera which <command>
  chimera exec <command> [args...]   # explicit passthrough to PATH
"""
import json, os, shutil, subprocess, sys

CATALOG = "/usr/share/chimera/commands/chimera-command-list.json"

def load():
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)

def all_commands(c):
    out=[]
    for names in c.get("categories", {}).values():
        out.extend(names)
    return sorted(set(out))

def native(c):
    return c.get("native_chimera", {}).get("commands", [])

def main(argv):
    c=load()
    cmds=all_commands(c)
    n=native(c)
    args=argv[1:]
    if not args or args[0] in ("help","--help","-h"):
        if len(args)>1:
            q=args[1]
            if q in n:
                print(f"{q}: native Chimera II OS control-plane command")
                print("Use the command's own --help when its implementation is installed.")
            elif q in cmds:
                print(f"{q}: Linux/Bash compatibility command; see 'man {q}' or 'help {q}' where available.")
            else:
                print(f"Unknown command: {q}", file=sys.stderr); return 1
        else:
            print("Chimera II OS command console")
            print("  chimera commands       List Linux/Bash compatibility commands")
            print("  chimera native         List native Chimera II OS commands")
            print("  chimera search TERM    Search both catalogs")
            print("  chimera which CMD      Resolve command in PATH")
            print("  chimera help CMD       Show command classification")
            print("  chimera exec CMD ...   Explicitly execute a PATH command")
        return 0
    op=args[0]
    if op == "commands":
        for x in cmds: print(x)
        return 0
    if op == "native":
        for x in n: print(x)
        return 0
    if op == "search":
        q=" ".join(args[1:]).lower()
        if not q: return 2
        for x in sorted(set(cmds+n)):
            if q in x.lower(): print(x)
        return 0
    if op == "which":
        if len(args)<2: return 2
        p=shutil.which(args[1])
        print(p or "not found")
        return 0 if p else 1
    if op == "exec":
        if len(args)<2: return 2
        return subprocess.call(args[1:])
    if op in ("version","--version","-V"):
        print("Chimera II OS command catalog 1.0")
        return 0
    print(f"Unknown chimera operation: {op}. Try: chimera help", file=sys.stderr)
    return 2

if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except FileNotFoundError as e:
        print(f"chimera: command catalog unavailable: {e}", file=sys.stderr)
        raise SystemExit(1)
