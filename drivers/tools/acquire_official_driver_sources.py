#!/usr/bin/env python3
"""Acquire external driver references without reporting partial checkouts as complete."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "foreign-source"
MANIFEST_DIR = ROOT / "manifests"

SOURCES = (
    ("linux", "https://github.com/torvalds/linux.git"),
    ("windows-driver-samples", "https://github.com/microsoft/Windows-driver-samples.git"),
    ("windows-rust-driver-samples", "https://github.com/microsoft/Windows-rust-driver-samples.git"),
)


def run_git(args):
    return subprocess.run(
        args,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def require_success(result, operation):
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "no diagnostic").strip()
        raise RuntimeError(
            f"{operation} exited {result.returncode}: {detail[-1000:]}"
        )
    return result.stdout.strip()


def acquire_source(name, url, out_dir):
    destination = Path(out_dir) / name
    try:
        if (destination / ".git").is_dir():
            require_success(
                run_git(["git", "-C", str(destination), "fetch", "--depth=1", "origin"]),
                "git fetch",
            )
            require_success(
                run_git(["git", "-C", str(destination), "reset", "--hard", "origin/HEAD"]),
                "git reset --hard",
            )
        else:
            require_success(
                run_git(["git", "clone", "--depth=1", "--filter=blob:none", url, str(destination)]),
                "git clone",
            )

        revision = require_success(
            run_git(["git", "-C", str(destination), "rev-parse", "HEAD"]),
            "git rev-parse HEAD",
        )
        if not revision:
            raise RuntimeError("git rev-parse HEAD returned an empty revision")
        return {
            "name": name,
            "url": url,
            "revision": revision,
            "status": "checked_out",
        }
    except (OSError, RuntimeError) as exc:
        return {
            "name": name,
            "url": url,
            "status": "checkout_failed",
            "working_tree_present": (destination / ".git").is_dir(),
            "error": str(exc)[:1200],
        }


def summarize(rows):
    return {
        "acquired": sum(row.get("status") == "checked_out" for row in rows),
        "failed": sum(row.get("status") == "checkout_failed" for row in rows),
        "reference_only": sum(row.get("status") == "reference_only" for row in rows),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    rows = [acquire_source(name, url, OUT) for name, url in SOURCES]
    rows.extend(
        (
            {
                "name": "apple-driverkit",
                "url": "https://developer.apple.com/documentation/driverkit",
                "status": "reference_only",
                "reason": "Apple SDK, signing and entitlement requirements",
            },
            {
                "name": "apple-system-extensions",
                "url": "https://developer.apple.com/documentation/SystemExtensions",
                "status": "reference_only",
                "reason": "Apple SDK, signing and entitlement requirements",
            },
        )
    )

    counts = summarize(rows)
    manifest = {
        "schema": "chimera-acquired-driver-sources-v2",
        "counts": counts,
        "sources": rows,
    }
    manifest_path = MANIFEST_DIR / "acquired-driver-sources.json"
    with manifest_path.open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")

    print(json.dumps(counts, sort_keys=True))
    for row in rows:
        if row.get("status") == "checkout_failed":
            print(
                f"DRIVER SOURCE CHECKOUT FAILED: {row['name']}: {row.get('error', 'unknown error')}",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
