#!/usr/bin/env python3
"""Chimera Sentinel: offline-first advisory intake and safe patch planning.

The tool never executes downloaded advisory content, applies arbitrary patches,
or performs unbounded Internet scanning. It records provenance and emits a
reviewable patch plan for the existing safe repair pipeline.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, time, urllib.request

SOURCES = {
    "github_advisories": "https://api.github.com/advisories",
    "nvd": "https://services.nvd.nist.gov/rest/json/cves/2.0",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_json(url: str, timeout: int = 15) -> tuple[dict | list, str]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "ChimeraIIOS-Sentinel/1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read(2_000_000)
    return json.loads(body), sha256_bytes(body)


def load_offline(path: pathlib.Path):
    raw = path.read_bytes()
    return json.loads(raw), sha256_bytes(raw)


def make_plan(advisories, source: str, digest: str, offline: bool) -> dict:
    items = advisories if isinstance(advisories, list) else advisories.get("vulnerabilities", advisories.get("data", []))
    return {
        "schema": "CHIMERA-SENTINEL-PLAN-1",
        "created_at": int(time.time()),
        "source": source,
        "source_sha256": digest,
        "offline": offline,
        "provenance_required": True,
        "automatic_execution": False,
        "automatic_merge": False,
        "automatic_network_mutation": False,
        "advisory_count": len(items) if isinstance(items, list) else 0,
        "actions": [
            "normalize_advisories",
            "match_installed_components",
            "generate_reviewable_patch_candidates",
            "sandbox_build_and_test",
            "security_regression_test",
            "stage_for_policy_approval",
            "rollback_on_failed_verification",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=sorted(SOURCES), default="github_advisories")
    parser.add_argument("--offline-file", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("data/security/sentinel_plan.json"))
    args = parser.parse_args()
    if args.offline_file:
        data, digest = load_offline(args.offline_file)
        source, offline = str(args.offline_file), True
    else:
        data, digest = fetch_json(SOURCES[args.source])
        source, offline = SOURCES[args.source], False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(make_plan(data, source, digest, offline), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
