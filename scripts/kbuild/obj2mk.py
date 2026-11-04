#!/usr/bin/env python3
"""Translate Linux-style Kbuild fragments into a make fragment for Koronos.

Walks kernel/ looking for Kbuild files, resolves obj-y / obj-m / obj-$(CONFIG_*)
assignments plus per-file KORONOS_CXXFLAGS_<obj>.o overrides, and emits a make
fragment describing every object to compile and link.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

LANG = {".cpp": "cxx", ".cc": "cxx", ".c": "cxx", ".asm": "asm", ".S": "asm"}
SOURCE_EXTS = (".cpp", ".cc", ".c", ".asm", ".S")


def resolve_source(base_dir, obj, root=None):
    """Map a Kbuild object entry (foo.o) to a real source file."""
    stem, ext = os.path.splitext(obj)
    if ext in LANG:
        candidate = os.path.join(base_dir, obj)
        return candidate if os.path.exists(candidate) else None
    for candidate_ext in SOURCE_EXTS:
        candidate = os.path.join(base_dir, stem + candidate_ext)
        if root and not os.path.exists(os.path.join(root, candidate)):
            continue
        if os.path.exists(os.path.join(root, candidate)) if root else os.path.exists(candidate):
            return candidate
    return None


def config_values(config_path):
    values = {}
    if config_path and os.path.exists(config_path):
        for line in open(config_path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip().strip('"')
    return values


def conditional_configs(expr, values):
    """Returns True when the obj-$(CONFIG_X) / obj-$(CONFIG_X:y) entry is enabled."""
    expr = expr.strip()
    if expr.startswith("CONFIG_"):
        val = values.get(expr, "n")
        return val not in ("n", "", None)
    if ":" in expr:
        name, want = expr.split(":", 1)
        return values.get(name, "n") == want
    return False


def parse_kbuild(path, values):
    entries = {"y": [], "m": []}
    flags = {}
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.match(r"obj-\$\(([^)]+)\)\s*[:+]?=\s*(.+)$", line)
        if match:
            cond, objs = match.group(1), match.group(2)
            kind = "m" if cond == "CONFIG_KORONOS_MODULES" else "y"
            if not conditional_configs(cond, values):
                continue
            entries[kind].extend(objs.split())
            continue
        match = re.match(r"obj-(y|m)\s*[:+]?=\s*(.+)$", line)
        if match:
            entries[match.group(1)].extend(match.group(2).split())
            continue
        match = re.match(r"(?:KORONOS_)?CXXFLAGS_([A-Za-z0-9_.-]+)\s*[:+]?=\s*(.+)$", line)
        if match:
            flags[match.group(1)] = match.group(2).strip()
    return entries, flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="repository root")
    ap.add_argument("--build", required=True, help="build directory")
    ap.add_argument("--config", default=None, help=".config path")
    ap.add_argument("--out", required=True, help="make fragment to write")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    kernel = os.path.join(args.root, "kernel")
    values = config_values(args.config or os.path.join(kernel, ".config"))

    objs, flags, seen = [], {}, set()
    for dirpath, dirnames, filenames in os.walk(kernel):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in ("generated",))
        if "Kbuild" not in filenames:
            continue
        entries, kflags = parse_kbuild(os.path.join(dirpath, "Kbuild"), values)
        rel_dir = os.path.relpath(dirpath, kernel)
        for obj in entries["y"]:
            resolved = resolve_source(rel_dir, obj, kernel)
            if resolved is None:
                continue
            src = os.path.normpath(resolved)
            stem, ext = os.path.splitext(src)
            lang = LANG.get(ext)
            if lang is None:
                continue
            if (src, "y") in seen:
                continue
            seen.add((src, "y"))
            objs.append({"src": src, "obj": stem + ".o", "lang": lang, "kind": "y"})
            for key in (os.path.basename(stem) + ".o", obj):
                if key in kflags:
                    flags[stem + ".o"] = kflags[key]
        for obj in entries["m"]:
            resolved = resolve_source(rel_dir, obj, kernel)
            if resolved is None:
                continue
            src = os.path.normpath(resolved)
            stem, ext = os.path.splitext(src)
            if LANG.get(ext) not in ("asm", "S"):
                continue
            objs.append({"src": src, "obj": stem + ".ko", "lang": "asm", "kind": "m"})

    if not objs:
        print("obj2mk: no objects discovered", file=sys.stderr)
        return 1

    lines = ["# generated by scripts/kbuild/obj2mk.py -- do not edit", ""]
    y_objs = [os.path.join("$(BUILD)", o["obj"]) for o in objs if o["kind"] == "y"]
    m_objs = [os.path.join("$(BUILD)", o["obj"]) for o in objs if o["kind"] == "m"]
    lines.append("KO_OBJS := \\")
    for i, obj in enumerate(y_objs):
        lines.append("\t%s%s" % (obj, " \\" if i < len(y_objs) - 1 else ""))
    lines.append("")
    lines.append("KO_MODULES := \\")
    for i, obj in enumerate(m_objs):
        lines.append("\t%s%s" % (obj, " \\" if i < len(m_objs) - 1 else ""))
    lines.append("")
    for obj, flag in sorted(flags.items()):
        lines.append("%s: KO_CFLAGS := %s" % (os.path.join("$(BUILD)", obj), flag))
    lines.append("")
    lines.append("KO_SOURCES := \\")
    for i, o in enumerate(objs):
        lines.append("\t%s%s" % (os.path.join("$(ROOT)/kernel", o["src"]), " \\" if i < len(objs) - 1 else ""))
    lines.append("")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump({"objects": objs, "flags": flags}, handle, indent=1)

    print("obj2mk: %d objects (%d modules) -> %s" % (len(y_objs), len(m_objs), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
