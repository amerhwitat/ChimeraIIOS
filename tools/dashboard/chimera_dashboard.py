#!/usr/bin/env python3
"""Portable, read-only dashboard snapshot helper for all Chimera II OS editions."""
from __future__ import annotations
import argparse
import json
import os
import platform
import time
from pathlib import Path

EDITIONS = ("desktop", "server", "mobile", "edge", "iot", "cvel")

def read_float(path: str, default: float = 0.0) -> float:
    try:
        return float(Path(path).read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return default

def memory_percent() -> float:
    total = available = 0.0
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "MemTotal:": total = float(parts[1])
            if len(parts) >= 2 and parts[0] == "MemAvailable:": available = float(parts[1])
    except OSError:
        pass
    return ((total - available) / total * 100.0) if total else 0.0

def snapshot(edition: str) -> dict:
    if edition not in EDITIONS:
        raise ValueError(f"unsupported edition: {edition}")
    uptime = read_float("/proc/uptime")
    cores = max(1, os.cpu_count() or 1)
    load = read_float("/proc/loadavg")
    return {
        "schema": "CHIMERA-DASHBOARD-SNAPSHOT-1",
        "timestamp": time.time(),
        "edition": edition,
        "architecture": platform.machine(),
        "uptime_seconds": int(uptime),
        "kpis": {
            "cpu.utilization": min(100.0, load / cores * 100.0),
            "memory.utilization": memory_percent(),
            "load.1m": load,
        },
        "policy": {"read_only": True, "remote_control": False},
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", choices=EDITIONS, default="desktop")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = snapshot(args.edition)
    text = json.dumps(data, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
