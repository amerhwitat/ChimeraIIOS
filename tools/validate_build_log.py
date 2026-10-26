#!/usr/bin/env python3
"""Fail-closed parser for boot/ISO artifact validation logs.

Accepted records:
  [VALIDATION RUN] command=<non-empty command>
  [VALIDATION PASS] exit=0 command=<same command>
  [VALIDATION FAIL] exit=<nonzero integer> command=<same command>

Non-validation command output is permitted between records. Lines beginning with
"[VALIDATION" must match the record grammar exactly. Every RUN must have one
matching result, no result may be orphaned, and required command fragments must
appear in successful records. This verifies log integrity, not artifact runtime.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RUN_RE = re.compile(r"^\[VALIDATION RUN\] command=(.+)$")
RESULT_RE = re.compile(r"^\[VALIDATION (PASS|FAIL)\] exit=([0-9]+) command=(.+)$")
PREFIX = "[VALIDATION"


class LogValidationError(ValueError):
    pass


def parse_validation_log(text: str, required: tuple[str, ...] = ()) -> dict:
    pending: dict[str, int] = {}
    passed: list[str] = []
    failed: list[tuple[str, int]] = []
    seen_commands: set[str] = set()
    records = 0

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.startswith(PREFIX):
            continue
        run = RUN_RE.fullmatch(line)
        result = RESULT_RE.fullmatch(line)
        if run:
            command = run.group(1).strip()
            if not command:
                raise LogValidationError(f"line {line_no}: empty RUN command")
            if command in pending:
                raise LogValidationError(f"line {line_no}: duplicate RUN before result: {command}")
            pending[command] = line_no
            seen_commands.add(command)
            records += 1
            continue
        if not result:
            raise LogValidationError(f"line {line_no}: malformed validation record")
        kind, exit_text, command = result.groups()
        # Shell process exit statuses are in the range 0..255. Bound the
        # parsed value explicitly so hostile logs cannot trigger huge-int errors.
        if len(exit_text) > 3:
            raise LogValidationError(f"line {line_no}: exit code out of range")
        exit_code = int(exit_text)
        if exit_code > 255:
            raise LogValidationError(f"line {line_no}: exit code out of range: {exit_code}")
        if command not in pending:
            raise LogValidationError(f"line {line_no}: orphan {kind} result: {command}")
        del pending[command]
        records += 1
        if kind == "PASS":
            if exit_code != 0:
                raise LogValidationError(f"line {line_no}: PASS requires exit=0")
            passed.append(command)
        else:
            if exit_code == 0:
                raise LogValidationError(f"line {line_no}: FAIL requires nonzero exit")
            failed.append((command, exit_code))

    if pending:
        details = ", ".join(f"{cmd!r} (RUN line {line})" for cmd, line in pending.items())
        raise LogValidationError(f"missing result for RUN record(s): {details}")
    if records == 0:
        raise LogValidationError("no validation records found")
    if failed:
        details = "; ".join(f"{cmd!r} exited {code}" for cmd, code in failed)
        raise LogValidationError(f"validator failure(s): {details}")

    missing = [fragment for fragment in required
               if not any(fragment in command for command in passed)]
    if missing:
        raise LogValidationError("required successful validation missing for: " +
                                 ", ".join(repr(item) for item in missing))
    return {"records": records, "passed": passed, "failed": failed,
            "commands": sorted(seen_commands)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="validation log to inspect")
    parser.add_argument("--require", action="append", default=[], metavar="TEXT",
                        help="require a successful command containing TEXT; repeatable")
    args = parser.parse_args(argv)
    try:
        text = args.log.read_text(encoding="utf-8")
        result = parse_validation_log(text, tuple(args.require))
    except (OSError, UnicodeError, LogValidationError) as exc:
        print(f"[VALIDATION LOG FAIL] {exc}", file=sys.stderr)
        return 1
    print(f"[VALIDATION LOG PASS] records={result['records']} successful={len(result['passed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
