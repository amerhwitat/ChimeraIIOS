#!/usr/bin/env python3
"""Fail-closed parser for boot/ISO artifact validation records.

This checks validation-log integrity, not whether the artifacts boot at runtime.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

_PREFIX = "[VALIDATION"
_RUN = re.compile(r"^\[VALIDATION RUN\] command=(.+)$")
_RESULT = re.compile(r"^\[VALIDATION (PASS|FAIL)\] exit=([0-9]+) command=(.+)$")


class LogValidationError(ValueError):
    """Raised when validation records are malformed or incomplete."""


def parse_validation_log(text: str, required: Iterable[str] = ()) -> dict:
    pending: dict[str, int] = {}
    passed: list[str] = []
    failed: list[tuple[str, int]] = []
    commands: set[str] = set()
    records = 0

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.startswith(_PREFIX):
            continue
        run = _RUN.fullmatch(line)
        result = _RESULT.fullmatch(line)
        if run:
            command = run.group(1).strip()
            if not command:
                raise LogValidationError(f"malformed validation record on line {line_no}")
            if command in pending:
                raise LogValidationError(f"duplicate RUN before result: {command}")
            pending[command] = line_no
            commands.add(command)
            records += 1
            continue
        if not result:
            raise LogValidationError(f"malformed validation record on line {line_no}")
        kind, exit_text, command = result.groups()
        if len(exit_text) > 3:
            raise LogValidationError(f"exit code out of range on line {line_no}")
        code = int(exit_text)
        if code > 255:
            raise LogValidationError(f"exit code out of range on line {line_no}")
        if kind == "PASS" and code != 0:
            raise LogValidationError("PASS requires exit=0")
        if kind == "FAIL" and code == 0:
            raise LogValidationError("FAIL requires nonzero exit")
        if command not in pending:
            raise LogValidationError(f"orphan {kind} result for {command!r}")
        del pending[command]
        records += 1
        if kind == "PASS":
            passed.append(command)
        else:
            failed.append((command, code))

    if records == 0:
        raise LogValidationError("no validation records found")
    if pending:
        command, line_no = next(iter(pending.items()))
        raise LogValidationError(f"missing result for {command!r} (RUN on line {line_no})")
    if failed:
        command, code = failed[0]
        raise LogValidationError(f"validation command {command!r} exited {code}")
    missing = [item for item in required if not any(item in cmd for cmd in passed)]
    if missing:
        raise LogValidationError(
            "missing required successful validation for: " + ", ".join(missing)
        )
    return {"records": records, "passed": passed, "failed": failed,
            "commands": sorted(commands)}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("usage: validate_build_log.py LOG [REQUIRED_ARTIFACT ...]", file=sys.stderr)
        return 2 if not args else 0
    path = Path(args[0])
    required: list[str] = []
    index = 1
    while index < len(args):
        if args[index] == "--require" and index + 1 < len(args):
            required.append(args[index + 1])
            index += 2
        else:
            required.append(args[index])
            index += 1
    try:
        log = path.read_bytes().decode("utf-8", errors="strict")
        result = parse_validation_log(log, required)
    except (OSError, UnicodeError, LogValidationError) as exc:
        print(f"[VALIDATION LOG FAIL] {exc}", file=sys.stderr)
        return 1
    print(f"[VALIDATION LOG PASS] records={result['records']} successful={len(result['passed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
