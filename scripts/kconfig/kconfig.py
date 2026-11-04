#!/usr/bin/env python3
"""Minimal Kconfig implementation for the Koronos kernel build.

Supports the subset used by kernel/Kconfig: config entries with bool/tristate/
string/int/hex types, prompt text, default, depends on, select, choice blocks,
menu/endmenu, if/endif, comment, source and help. Values are resolved with the
same tristate semantics as the Linux kernel configuration system for the
constructs that appear here.

Usage:
    kconfig.py defconfig   <Kconfig> <.config> [--srctree DIR]
    kconfig.py oldconfig   <Kconfig> <.config> [--srctree DIR]
    kconfig.py menuconfig  <Kconfig> <.config> [--srctree DIR]
    kconfig.py savedefconfig <Kconfig> <.config> [--srctree DIR]
    kconfig.py autoconf    <Kconfig> <.config> <auto.conf> <autoconf.h> [--srctree DIR]
"""
from __future__ import annotations

import json
import os
import re
import sys

TRISTATE = {"n": 0, "m": 1, "y": 2}
INVERT = {v: k for k, v in TRISTATE.items()}


class Entry:
    def __init__(self, name, kind="bool"):
        self.name = name
        self.kind = kind
        self.prompt = ""
        self.defaults = []
        self.depends = ""
        self.selects = []
        self.help = ""
        self.range = None
        self.visible = True

    def __repr__(self):
        return "<Entry %s %s>" % (self.name, self.kind)


def strip_comment(line):
    out, quote = [], False
    for ch in line:
        if ch == '"':
            quote = not quote
        if ch == "#" and not quote:
            break
        out.append(ch)
    return "".join(out)


def tokenize_value(expr, values):
    """Evaluate a Kconfig expression to a tristate int."""
    expr = (expr or "").strip()
    if not expr:
        return 2
    if expr in TRISTATE:
        return TRISTATE[expr]
    expr = expr.replace("&&", " and ").replace("||", " or ")
    expr = re.sub(r"!(?!=)", " not ", expr)

    def repl(match):
        sym = match.group(0)
        if sym in ("and", "or", "not"):
            return sym
        if sym in values:
            return str(TRISTATE.get(str(values[sym]).lower(), 2))
        return "0"

    try:
        result = eval(re.sub(r"[A-Za-z_][A-Za-z0-9_]*", repl, expr), {"__builtins__": {}}, {})
    except Exception:
        return 2
    if isinstance(result, str):
        return TRISTATE.get(result.lower(), 2)
    return TRISTATE["y"] if result else TRISTATE["n"]


def parse(path, srctree, entries, order, choices, depth=0):
    if depth > 12:
        raise SystemExit("Kconfig include depth exceeded at %s" % path)
    current = None
    in_help = False
    help_indent = None
    pending_depends = []
    choice_stack = []
    if_stack = []
    active = True

    def flush():
        nonlocal current
        if current is not None:
            current = None

    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            stripped = strip_comment(line).strip()

            if in_help:
                if stripped == "" or raw.startswith((" ", "\t")):
                    if current is not None and stripped:
                        current.help += stripped + "\n"
                    continue
                in_help = False

            if not stripped:
                continue

            if stripped in ("menuconfig",) or stripped.startswith("menuconfig "):
                stripped = "config " + stripped[len("menuconfig "):]

            if stripped.startswith(("config ", "menuconfig ")):
                flush()
                name = stripped.split(None, 1)[1].strip()
                current = Entry(name)
                entries[name] = current
                order.append(name)
                for dep in pending_depends:
                    current.depends = (current.depends + " && " + dep).strip(" &")
                if choice_stack:
                    current.depends = (current.depends + " && " + choice_stack[-1]).strip(" &")
                if not active:
                    current.visible = False
                continue

            if current is None:
                if stripped.startswith("source "):
                    match = re.match(r'source\s+"?([^"]+)"?', stripped)
                    if match:
                        target = os.path.join(srctree, match.group(1))
                        if os.path.exists(target):
                            parse(target, srctree, entries, order, choices, depth + 1)
                    continue
                if stripped.startswith("choice"):
                    choices.append({"name": stripped.split(None, 1)[1] if " " in stripped else "", "entries": []})
                    continue
                if stripped.startswith(("bool ", "tristate ")):
                    if choices:
                        choices[-1]["type"] = stripped.split()[0]
                    continue
                if stripped in ("endchoice", "endmenu", "endif"):
                    if stripped == "endif" and if_stack:
                        active = if_stack.pop()
                    continue
                if stripped.startswith("if "):
                    if_stack.append(active)
                    active = active and tokenize_value(stripped[3:], {}) > 0
                    continue
                if stripped.startswith("depends on ") and choices:
                    choices[-1].setdefault("depends", []).append(stripped[len("depends on "):])
                    continue
                continue

            if stripped.startswith("bool"):
                current.kind = "bool"
                match = re.search(r'"(.*)"', stripped)
                if match:
                    current.prompt = match.group(1)
            elif stripped.startswith("tristate"):
                current.kind = "tristate"
                match = re.search(r'"(.*)"', stripped)
                if match:
                    current.prompt = match.group(1)
            elif stripped.startswith("string"):
                current.kind = "string"
                match = re.search(r'"(.*)"', stripped)
                if match:
                    current.prompt = match.group(1)
            elif stripped.startswith(("int", "hex")):
                current.kind = "int"
                match = re.search(r'"(.*)"', stripped)
                if match:
                    current.prompt = match.group(1)
            elif stripped.startswith("default "):
                current.defaults.append(stripped[len("default "):].strip().strip('"'))
            elif stripped.startswith("depends on "):
                dep = stripped[len("depends on "):]
                current.depends = (current.depends + " && " + dep).strip(" &")
            elif stripped.startswith("select "):
                current.selects.append(stripped[len("select "):].split()[0])
            elif stripped.startswith("range "):
                current.range = stripped[len("range "):]
            elif stripped.startswith("help") or stripped.startswith("---help---"):
                in_help = True
            elif stripped.startswith("prompt "):
                match = re.search(r'"(.*)"', stripped)
                if match:
                    current.prompt = match.group(1)
            elif stripped in ("endchoice", "endmenu"):
                if stripped == "endchoice" and choices:
                    choices.pop()
                flush()

    if choices:
        # record choice membership for menuconfig rendering
        pass


def load_config(path):
    values = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                values[key.replace("CONFIG_", "")] = val.strip().strip('"')
    return values


def resolve(entries, order, values, use_defaults):
    for name in order:
        entry = entries[name]
        enabled = tokenize_value(entry.depends, values) > 0 and entry.visible
        if not enabled:
            values[name] = "n"
            continue
        if use_defaults or name not in values or values.get(name) in (None, ""):
            chosen = None
            for default in entry.defaults:
                if entry.kind in ("bool", "tristate"):
                    chosen = INVERT[tokenize_value(default, values)]
                else:
                    chosen = os.path.expandvars(default)
                break
            if chosen is None:
                chosen = "n" if entry.kind in ("bool", "tristate") else ""
            values[name] = chosen
        if entry.kind in ("bool", "tristate") and values[name] not in TRISTATE:
            values[name] = "y" if str(values[name]).lower() in ("y", "yes", "true", "1") else "n"
        if values[name] not in ("n", ""):
            for selected in entry.selects:
                values[selected] = "y"
    return values


def write_config(path, order, entries, values):
    lines = ["#", "# Automatically generated file; DO NOT EDIT.", "# Koronos kernel configuration", "#"]
    for name in order:
        entry = entries[name]
        val = values.get(name, "n")
        if entry.kind in ("bool", "tristate"):
            lines.append("# CONFIG_%s is not set" % name if val == "n" else "CONFIG_%s=%s" % (name, val))
        else:
            if val and str(val).lstrip("-").isdigit():
                lines.append("CONFIG_%s=%s" % (name, val))
            elif val:
                lines.append('CONFIG_%s="%s"' % (name, val))
            else:
                lines.append("# CONFIG_%s is not set" % name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_auto_conf(config_path, auto_path, header_path, order, entries, values):
    os.makedirs(os.path.dirname(auto_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(header_path) or ".", exist_ok=True)
    with open(auto_path, "w", encoding="utf-8") as handle:
        for name in order:
            val = values.get(name, "n")
            if val and val != "n":
                handle.write("CONFIG_%s=%s\n" % (name, val))
    with open(header_path, "w", encoding="utf-8") as handle:
        handle.write("/* Automatically generated; do not edit. */\n#ifndef KORONOS_AUTOCONF_H\n#define KORONOS_AUTOCONF_H\n")
        for name in order:
            val = values.get(name, "n")
            if val in ("y", "m"):
                handle.write("#define CONFIG_%s 1\n" % name)
            elif val and val != "n":
                handle.write('#define CONFIG_%s "%s"\n' % (name, val))
        handle.write("#endif\n")


def menuconfig(order, entries, values):
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not interactive:
        print("menuconfig: no TTY, keeping existing configuration (oldconfig behaviour)")
        return values
    while True:
        print("\nKoronos kernel configuration")
        print("-" * 60)
        visible = [n for n in order if entries[n].visible]
        for idx, name in enumerate(visible, 1):
            entry = entries[name]
            mark = "[%s]" % values.get(name, "n") if entry.kind in ("bool", "tristate") else "[%s]" % values.get(name, "")
            print(" %2d. %-40s %s" % (idx, entry.name, mark))
        print("  s. save and exit\n  q. quit without saving")
        answer = input("select> ").strip().lower()
        if answer in ("s", ""):
            return values
        if answer == "q":
            raise SystemExit(1)
        if answer.isdigit() and 1 <= int(answer) <= len(visible):
            name = visible[int(answer) - 1]
            entry = entries[name]
            if entry.kind in ("bool", "tristate"):
                values[name] = "n" if values.get(name) == "y" else "y"
            else:
                values[name] = input("%s value [%s]> " % (name, values.get(name, ""))).strip() or values.get(name, "")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    command, kconfig_path, config_path = argv[1], argv[2], argv[3]
    srctree = os.path.dirname(os.path.dirname(os.path.abspath(kconfig_path)))
    if "--srctree" in argv:
        srctree = argv[argv.index("--srctree") + 1]

    entries, order, choices = {}, [], []
    parse(kconfig_path, srctree, entries, order, choices)
    values = load_config(config_path)

    if command == "defconfig":
        values = resolve(entries, order, {}, use_defaults=True)
        write_config(config_path, order, entries, values)
    elif command == "oldconfig":
        values = resolve(entries, order, values, use_defaults=False)
        write_config(config_path, order, entries, values)
    elif command == "menuconfig":
        values = resolve(entries, order, values, use_defaults=False)
        values = menuconfig(order, entries, values)
        values = resolve(entries, order, values, use_defaults=False)
        write_config(config_path, order, entries, values)
    elif command == "savedefconfig":
        values = resolve(entries, order, values, use_defaults=False)
        target = config_path if config_path.endswith("defconfig") else "defconfig"
        write_config(target, order, entries, values)
        print("saved %s" % target)
    elif command == "autoconf":
        values = resolve(entries, order, values, use_defaults=False)
        auto_path, header_path = argv[4], argv[5]
        write_auto_conf(config_path, auto_path, header_path, order, entries, values)
    else:
        print("unknown command: %s" % command)
        return 2

    enabled = sum(1 for name in order if values.get(name) not in ("n", "", None))
    print("kconfig: %s -> %s (%d/%d symbols enabled)" % (command, config_path, enabled, len(order)))
    summary = {"symbols": len(order), "enabled": enabled, "config": values}
    with open(config_path + ".json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
