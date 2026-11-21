#!/usr/bin/env python3
"""Koronos self-heal controller: bounded telemetry triage and gated recovery.

Input is JSON Lines. This tool never executes a repair unless --apply is supplied,
the service is allowlisted by policy, and an explicit adapter command is configured.
Learning backends are extension points; this baseline does not claim a trained RNN/LLM/RL model.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

SERVICE_RE = re.compile(r"^[A-Za-z0-9_.@-]+\.service$")
EVENT_TYPES = {"heartbeat", "service_failed", "service_stalled", "kernel_fault", "boot_marker"}


def load_policy(path: str | None) -> dict[str, Any]:
    if not path:
        return {
            "schema": "KORONOS-SELF-HEAL-1",
            "heartbeat_timeout_seconds": 30,
            "failure_window_seconds": 300,
            "max_restarts_per_window": 2,
            "restart_allowlist": [],
            "critical_services": ["kore.service"],
        }
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "KORONOS-SELF-HEAL-1":
        raise ValueError("unsupported self-heal policy schema")
    for key in ("heartbeat_timeout_seconds", "failure_window_seconds", "max_restarts_per_window"):
        if not isinstance(data.get(key), int) or data[key] < 1:
            raise ValueError(f"policy {key} must be a positive integer")
    if not isinstance(data.get("restart_allowlist"), list):
        raise ValueError("restart_allowlist must be a list")
    if any(not isinstance(s, str) or not SERVICE_RE.fullmatch(s) for s in data["restart_allowlist"]):
        raise ValueError("restart_allowlist contains an invalid service name")
    return data


def parse_events(stream: Any) -> list[dict[str, Any]]:
    events = []
    for line_no, line in enumerate(stream, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
        if not isinstance(event, dict) or event.get("type") not in EVENT_TYPES:
            raise ValueError(f"line {line_no}: event must be an object with supported type")
        service = event.get("service")
        if service is not None and (not isinstance(service, str) or not SERVICE_RE.fullmatch(service)):
            raise ValueError(f"line {line_no}: invalid service identifier")
        event["timestamp"] = float(event.get("timestamp", time.time()))
        events.append(event)
    return events


def build_plan(events: list[dict[str, Any]], policy: dict[str, Any], now: float | None = None) -> list[dict[str, Any]]:
    now = time.time() if now is None else now
    last_heartbeat: dict[str, float] = {}
    failures: dict[str, list[float]] = defaultdict(list)
    explicit_stalls: dict[str, float] = {}
    for event in events:
        service = event.get("service")
        if not service:
            continue
        ts = event["timestamp"]
        if event["type"] == "heartbeat":
            last_heartbeat[service] = max(ts, last_heartbeat.get(service, 0))
        elif event["type"] in {"service_failed", "service_stalled"}:
            failures[service].append(ts)
            if event["type"] == "service_stalled":
                explicit_stalls[service] = max(ts, explicit_stalls.get(service, 0))

    plans = []
    timeout = policy["heartbeat_timeout_seconds"]
    window = policy["failure_window_seconds"]
    max_restarts = policy["max_restarts_per_window"]
    allowlist = set(policy.get("restart_allowlist", []))
    for service in sorted(set(last_heartbeat) | set(failures) | set(explicit_stalls)):
        recent = [ts for ts in failures[service] if 0 <= now - ts <= window]
        heartbeat_age = now - last_heartbeat[service] if service in last_heartbeat else None
        stalled = service in explicit_stalls or (heartbeat_age is not None and heartbeat_age > timeout)
        if not stalled and not recent:
            continue
        reason = "heartbeat-timeout" if stalled and heartbeat_age is not None and heartbeat_age > timeout else (
            "explicit-stall" if stalled else "repeated-failure"
        )
        action = "observe"
        if stalled or len(recent) >= 2:
            action = "restart" if service in allowlist and len(recent) < max_restarts else "quarantine-and-report"
        plans.append({
            "service": service,
            "reason": reason,
            "heartbeat_age_seconds": round(heartbeat_age, 3) if heartbeat_age is not None else None,
            "recent_failures": len(recent),
            "action": action,
            "requires_operator_review": action != "restart",
        })
    return plans


def execute_plan(plans: list[dict[str, Any]], adapter: list[str] | None, apply: bool) -> list[dict[str, Any]]:
    results = []
    for plan in plans:
        result = dict(plan)
        if plan["action"] != "restart" or not apply:
            result["execution"] = "not-requested" if not apply else "policy-blocked"
        elif not adapter:
            result["execution"] = "blocked-no-adapter"
            result["requires_operator_review"] = True
        else:
            argv = []
            for token in adapter:
                argv.append(token.replace("{action}", "restart").replace("{service}", plan["service"]))
            try:
                completed = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=30)
                result["execution"] = "request-accepted-unverified" if completed.returncode == 0 else "failed"
                result["exit_code"] = completed.returncode
                result["output"] = (completed.stdout + completed.stderr)[-2000:]
                # A zero exit code means the adapter accepted the request, not that
                # the service recovered. A later heartbeat/status probe must verify it.
                result["requires_operator_review"] = True
            except (OSError, subprocess.TimeoutExpired) as exc:
                result["execution"] = "failed"
                result["error"] = str(exc)
                result["requires_operator_review"] = True
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", help="JSON policy file")
    parser.add_argument("--events", default="-", help="JSONL telemetry file, or - for stdin")
    parser.add_argument("--adapter-command", help="explicit command template; use {action} and {service} placeholders")
    parser.add_argument("--apply", action="store_true", help="execute allowlisted recovery actions (requires adapter)")
    parser.add_argument("--now", type=float, help="fixed epoch time for reproducible tests")
    args = parser.parse_args()
    if args.apply and not args.adapter_command:
        parser.error("--apply requires --adapter-command; no host service manager is assumed")
    try:
        policy = load_policy(args.policy)
        if args.events == "-":
            events = parse_events(sys.stdin)
        else:
            with open(args.events, encoding="utf-8") as stream:
                events = parse_events(stream)
        plans = build_plan(events, policy, args.now)
        results = execute_plan(plans, shlex.split(args.adapter_command) if args.adapter_command else None, args.apply)
        print(json.dumps({"schema": "KORONOS-SELF-HEAL-REPORT-1", "event_count": len(events), "plans": results}, indent=2))
        return 1 if any(x.get("execution") == "failed" for x in results) else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"koronos-self-heal: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
