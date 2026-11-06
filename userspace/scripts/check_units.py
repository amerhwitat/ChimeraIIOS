#!/usr/bin/env python3
"""Contract checks for the Aurora userspace units and helpers.

Validates the structure systemd itself tolerates but that silently breaks a
boot: missing sections, ExecStart pointing at a non-installed helper, unknown
WantedBy targets, and dangling instance units.
"""
from __future__ import annotations

import argparse
import configparser
import os
import sys

SYSTEM_TARGETS = {"multi-user.target", "graphical.target", "basic.target", "sysinit.target",
                  "local-fs.target", "network-online.target", "default.target", "shutdown.target"}
SERVICE_SUFFIXES = (".service", ".target", ".socket", ".timer", ".mount")


def parse_unit(path):
    parser = configparser.ConfigParser(strict=False, interpolation=None, delimiters=("=",))
    parser.optionxform = str
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--helpers", required=True)
    args = ap.parse_args()

    errors = []
    unit_names = set()
    units = {}

    for name in sorted(os.listdir(args.units)):
        if not name.endswith(SERVICE_SUFFIXES):
            continue
        path = os.path.join(args.units, name)
        unit_names.add(name)
        try:
            parser = parse_unit(path)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s: unparsable (%s)" % (name, exc))
            continue
        if not parser.has_section("Unit"):
            errors.append("%s: missing [Unit]" % name)
        elif not parser.get("Unit", "Description", fallback="").strip():
            errors.append("%s: missing Description=" % name)
        units[name] = parser

    helpers = {os.path.basename(p): p for p in
               (os.path.join(args.helpers, f) for f in os.listdir(args.helpers))
               if os.path.isfile(p)}
    for helper, path in helpers.items():
        if not os.access(path, os.X_OK):
            errors.append("%s: helper is not executable" % helper)

    for name, parser in units.items():
        service = parser["Service"] if parser.has_section("Service") else None
        if name.endswith(".service") and service is None:
            errors.append("%s: .service without [Service]" % name)
        if service is not None:
            exec_start = service.get("ExecStart", fallback="").strip()
            if not exec_start:
                errors.append("%s: missing ExecStart=" % name)
            else:
                binary = exec_start.split()[0].lstrip("-@+!:")
                base = os.path.basename(binary)
                if binary.startswith("/") and not os.path.exists(os.path.join(args.helpers, base)) \
                        and base not in ("startx", "openbox", "xsetroot", "feh", "xset", "ip", "sh", "python3"):
                    errors.append("%s: ExecStart binary is not provided by userspace/: %s" % (name, binary))
        if parser.has_section("Install"):
            for key in ("WantedBy", "RequiredBy"):
                value = parser.get("Install", key, fallback="")
                for target in value.split():
                    if target.endswith(".target") and target not in unit_names and target not in SYSTEM_TARGETS:
                        errors.append("%s: %s references unknown target %s" % (name, key, target))

    for parser_owner in ("jasper.target", "gates.target", "aurora.target"):
        if parser_owner not in units:
            errors.append("%s: desktop profile target is missing" % parser_owner)

    if errors:
        for err in errors:
            print("  FAIL %s" % err, file=sys.stderr)
        print("userspace check: FAILED (%d issue(s))" % len(errors), file=sys.stderr)
        return 1

    print("userspace check: OK -- %d units, %d helpers" % (len(units), len(helpers)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
