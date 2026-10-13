#!/usr/bin/env python3
"""Discover public DOS software and stage only explicitly approved, verified payloads.

Discovery is metadata-only. Binary inclusion requires an exact HTTPS package URL,
a reviewed redistribution license, a pinned SHA-256, redistributable=true, and a
smoke-tested manifest status. Archives are extracted with path-traversal defenses.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import time
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import zipfile

DEFAULT_SOURCE = "https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/repositories/latest/html/en/games/index.html"
ALLOWED_HOSTS = {"www.ibiblio.org", "ibiblio.org", "www.freedos.org", "freedos.org"}
DOS_EXTENSIONS = {".com", ".exe", ".bat", ".sys", ".cfg", ".dat", ".txt", ".doc", ".hlp", ".wad", ".mid", ".voc", ".ogg", ".bmp", ".pcx", ".pal", ".lmp", ".deh"}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.items = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []
    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            label = " ".join(" ".join(self.text).split())
            self.items.append({"title": label, "url": self.href})
            self.href = None
            self.text = []

def fetch(url: str, timeout: int = 25) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"HTTPS URL required: {url}")
    req = Request(url, headers={"User-Agent": "Chimera-DOS-Payload-Builder/1.0"})
    with urlopen(req, timeout=timeout) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https":
            raise ValueError("redirected away from HTTPS")
        return response.read(16 * 1024 * 1024 + 1)

def discover(source: str, output: Path) -> int:
    raw = fetch(source)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("source page exceeds 16 MiB limit")
    parser = Links()
    parser.feed(raw.decode("utf-8", errors="replace"))
    rows = []
    for item in parser.items:
        url = urljoin(source, item["url"])
        p = urlparse(url)
        if p.scheme == "https" and p.hostname in ALLOWED_HOSTS and item["title"]:
            rows.append({"title": html.unescape(item["title"]), "url": url})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema_version": 1, "source_url": source, "retrieved_unix": int(time.time()),
        "discovery_only": True,
        "notice": "Discovery does not approve redistribution, download binaries, or assert runtime compatibility.",
        "links": rows,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Discovered {len(rows)} links; metadata only -> {output}")
    return 0

def safe_id(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", value))

def valid_payload(item: dict) -> bool:
    url = item.get("package_url", "")
    parsed = urlparse(url) if isinstance(url, str) else None
    return bool(
        safe_id(str(item.get("id", "")))
        and item.get("status") == "smoke-tested"
        and item.get("license_reviewed") is True
        and item.get("redistributable") is True
        and item.get("smoke_tested") is True
        and isinstance(item.get("license"), str) and item["license"].strip()
        and isinstance(item.get("sha256"), str) and re.fullmatch(r"[0-9a-fA-F]{64}", item["sha256"])
        and parsed and parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS
        and parsed.username is None and parsed.password is None
        and item.get("format") == "zip"
    )

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_extract(archive: Path, destination: Path) -> int:
    count = 0
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            rel = PurePosixPath(name)
            if rel.is_absolute() or not rel.parts or any(p in ("", ".", "..") for p in rel.parts):
                raise ValueError(f"unsafe archive path: {info.filename}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"symlink entry is not allowed: {info.filename}")
            target = (root / Path(*rel.parts)).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"archive path escapes destination: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.suffix.lower() not in DOS_EXTENSIONS:
                continue
            if info.file_size > 64 * 1024 * 1024:
                raise ValueError(f"file exceeds 64 MiB limit: {info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
    return count

def stage(manifest_path: Path, cache: Path, destination: Path, allow_fetch: bool) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = list(manifest.get("bundled_titles", []))
    entries += [x for x in manifest.get("cataloged_titles", []) if isinstance(x, dict)]
    cache.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    index = []
    included = 0
    for item in entries:
        if not isinstance(item, dict) or not valid_payload(item):
            continue
        payload = cache / (item["id"] + ".zip")
        if not payload.is_file() and allow_fetch:
            try:
                data = fetch(item["package_url"])
                if len(data) > 256 * 1024 * 1024:
                    raise ValueError("package exceeds 256 MiB limit")
                payload.write_bytes(data)
            except (OSError, URLError, ValueError) as exc:
                print(f"skip {item.get('id')}: download failed: {exc}", file=sys.stderr)
                continue
        if not payload.is_file():
            continue
        if sha256(payload).lower() != item["sha256"].lower():
            print(f"skip {item['id']}: SHA-256 mismatch", file=sys.stderr)
            continue
        target = destination / item["id"]
        if target.exists():
            shutil.rmtree(target)
        try:
            files = safe_extract(payload, target)
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            shutil.rmtree(target, ignore_errors=True)
            print(f"skip {item['id']}: unsafe/invalid package: {exc}", file=sys.stderr)
            continue
        if files == 0:
            shutil.rmtree(target, ignore_errors=True)
            print(f"skip {item['id']}: no allowlisted DOS files", file=sys.stderr)
            continue
        included += 1
        index.append({
            "id": item["id"], "name": item.get("name", item["id"]),
            "license": item["license"], "source_url": item["package_url"],
            "sha256": item["sha256"].lower(), "files_staged": files,
            "launch_hint": "Use chimera-dos-adapter.py --run with a staged .COM/.EXE/.BAT file."
        })
    (destination / "CATALOG.json").write_text(json.dumps({
        "schema_version": 1, "included_payload_count": included,
        "items": index,
        "note": "Only explicitly license-reviewed, redistributable, hash-pinned and smoke-tested packages are staged."
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {included} approved DOS payload(s) into {destination}")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    d = sub.add_parser("discover", help="fetch public catalog metadata only")
    d.add_argument("--source", default=DEFAULT_SOURCE)
    d.add_argument("--output", type=Path, default=Path("build/dos-online-discovery.json"))
    s = sub.add_parser("stage", help="stage approved payloads from a verified manifest/cache")
    s.add_argument("--manifest", type=Path, required=True)
    s.add_argument("--cache", type=Path, required=True)
    s.add_argument("--dest", type=Path, required=True)
    s.add_argument("--fetch", action="store_true", help="download missing packages only when manifest approvals and SHA-256 are pinned")
    args = ap.parse_args()
    try:
        if args.command == "discover":
            return discover(args.source, args.output)
        return stage(args.manifest, args.cache, args.dest, args.fetch)
    except (OSError, ValueError, json.JSONDecodeError, URLError) as exc:
        print(f"dos-payload-builder: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
