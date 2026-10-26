#!/usr/bin/env python3
"""Prevent automatic container publication before the closing production DAPS gate."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    ROOT / ".github/workflows/docker-build.yml",
    ROOT / ".github/workflows/container.yml",
)


def main() -> int:
    for path in WORKFLOWS:
        if not path.is_file():
            print(f"CONTAINER PUBLISH FAIL: workflow missing: {path.name}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        required = (
            "workflow_dispatch:",
            "evidence_run_id:",
            "evidence_artifact_name:",
            "actions/download-artifact@v4",
            "tools/release/verify-production-daps.py --evidence build/production-daps/evidence.json",
            "steps.daps.outputs.accepted == 'true'",
        )
        for token in required:
            if token not in text:
                print(f"CONTAINER PUBLISH FAIL: {path.name} missing {token}", file=sys.stderr)
                return 1
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "push:":
                continue  # Top-level GitHub Actions event trigger, not a registry push.
            if stripped.startswith("push:") and "steps.daps.outputs.accepted == 'true'" not in stripped:
                print(f"CONTAINER PUBLISH FAIL: ungated push in {path.name}: {stripped}", file=sys.stderr)
                return 1
    print("CONTAINER PUBLISH PASS: both registry workflows require manual dispatch and successful production DAPS evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
