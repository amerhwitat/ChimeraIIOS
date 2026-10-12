#!/usr/bin/env python3
"""Bounded ISA/architecture discovery for Aurora; discoveries are proposals, never executable support."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = ROOT / "config" / "architecture-discovery" / "sources.json"
DEFAULT_PROFILES = ROOT / "config" / "compatibility" / "distro-desktop-profiles.json"
DEFAULT_OUTPUT = ROOT / "build" / "architecture-discovery"
MAX_BYTES = 1_500_000
TIMEOUT_SECONDS = 8
USER_AGENT = "ChimeraIIOS-ArchitectureDiscovery/1.0"
ALLOWED_HOSTS = {
    "github.com", "raw.githubusercontent.com", "riscv.org", "developer.arm.com",
    "intel.com", "www.intel.com", "docs.kernel.org", "kernel.org",
    "llvm.org", "qemu.org", "wiki.qemu.org", "loongson.cn",
    "openpower.foundation", "openrisc.io", "mips.com",
}
TERMS = re.compile(
    r"\b(x86[- ]?64|x86|aarch64|armv\d+|risc[- ]?v|mips|power isa|powerpc|"
    r"sparc|loongarch|xtensa|avr|superh|openrisc|s390x|webassembly|wasm|"
    r"vector extension|instruction set architecture|isa extension)\b", re.I
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_text(data: bytes) -> str:
    return SPACE_RE.sub(" ", TAG_RE.sub(" ", data.decode("utf-8", errors="replace"))).strip()


def source_host(url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"only HTTPS source URLs are allowed: {url}")
    host = parsed.hostname.lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"source host is not allowlisted: {host}")
    return host


def fetch_source(url: str) -> tuple[str, str]:
    source_host(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        final_host = source_host(final_url)
        content_type = response.headers.get("Content-Type", "")
        if not any(kind in content_type.lower() for kind in ("text/", "json", "xml")):
            raise ValueError(f"refusing non-text source type: {content_type}")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError(f"source exceeds {MAX_BYTES} byte limit")
    return normalized_text(payload), final_host


def walk_records(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_records(child)


def local_inventory(database_paths: list[Path]) -> list[dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in database_paths:
        if not path.is_file():
            continue
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        for row in walk_records(data):
            family = next((row.get(k) for k in ("family", "architecture", "architecture_name", "isa", "name") if isinstance(row.get(k), str) and row.get(k).strip()), None)
            if not family:
                continue
            label = family.strip()
            key = label.casefold()
            records.setdefault(key, {"name": label, "source_file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "status": "cataloged"})
    return sorted(records.values(), key=lambda item: item["name"].casefold())


def scan(sources: dict, database_paths: list[Path], online: bool) -> dict:
    inventory = local_inventory(database_paths)
    known = {item["name"].casefold() for item in inventory}
    findings: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources.get("sources", []):
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            errors.append({"source": "configuration", "error": "invalid source record"})
            continue
        url = source["url"]
        if not online:
            findings.append({"title": source.get("title", url), "url": url, "status": "not-checked-offline", "candidates": []})
            continue
        try:
            text, host = fetch_source(url)
            terms = sorted({m.group(0).strip() for m in TERMS.finditer(text)}, key=str.casefold)
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            findings.append({
                "title": source.get("title", url), "url": url, "host": host,
                "status": "source-checked-candidates-only", "sha256": digest,
                "candidates": [{"name": term, "status": "candidate-only", "requires_review": True} for term in terms],
            })
            for term in terms:
                if term.casefold() not in known:
                    known.add(term.casefold())
                    inventory.append({"name": term, "source_file": url, "status": "candidate-only"})
        except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            errors.append({"source": url, "error": str(exc)})
    return {
        "schema": "CHIMERA-ARCH-DISCOVERY-1", "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "online-bounded" if online else "offline",
        "policy": "Discovery is metadata only. It never downloads or executes compiler, driver, firmware, or kernel code and never promotes a candidate to supported.",
        "inventory": inventory, "sources": findings, "errors": errors,
        "compatibility_proposals": [
            {"architecture": item["name"], "status": "proposal-only", "decoder": "not-verified",
             "execution_backend": "not-verified", "conformance": "not-tested",
             "next_action": "review normative specification, implement backend, run tests"}
            for item in inventory if item.get("status") == "candidate-only"
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--database", type=Path, action="append", default=[])
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--online", action="store_true", help="check allowlisted HTTPS text sources; default is offline")
    parser.add_argument("--strict", action="store_true", help="fail if any configured source could not be checked")
    args = parser.parse_args()
    databases = args.database or [ROOT / "isa" / "isa_database.json", ROOT / "data" / "isa" / "isa_database.json"]
    try:
        source_config = load_json(args.sources)
        if args.profiles.exists():
            profiles = load_json(args.profiles)
            if not isinstance(profiles.get("profiles"), list):
                raise ValueError("distro desktop profile manifest must contain a profiles list")
        report = scan(source_config, databases, args.online)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        target = args.output_dir / "architecture-discovery-report.json"
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[architecture-discovery] mode={report['mode']} inventory={len(report['inventory'])} sources={len(report['sources'])} errors={len(report['errors'])} output={target}")
        if args.strict and report["errors"]:
            return 1
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[architecture-discovery] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
