#!/usr/bin/env python3
"""Stage the complete media/app/document/CI payload into a native ISO tree.

The boot payload (kernel, target inits, initramfs) is what makes the image run;
this stage makes the image *complete*: every wallpaper, icon, screenshot, video,
app catalogue, document and CI workflow is copied under /payload with a manifest
and per-file digests so the media can be verified from inside the image.

Usage: stage_payload.py --root <repo> --iso <iso-tree> [--limit-mb 200]
"""
import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico", ".bmp", ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".woff", ".woff2", ".ttf"}
APP_EXT = {".json", ".html", ".js", ".css"}
DOC_EXT = {".md", ".txt", ".pdf"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root, subdirs, exts):
    out = []
    for sub in subdirs:
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            if any(part in dirpath for part in ("/build/", "/.git/", "/node_modules/", "/dist/")):
                continue
            for name in filenames:
                if os.path.splitext(name)[1].lower() in exts:
                    path = os.path.join(dirpath, name)
                    if os.path.isfile(path) and not os.path.islink(path):
                        out.append((sub, path))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--limit-mb", type=float, default=200.0)
    args = ap.parse_args()

    budget = int(args.limit_mb * 1024 * 1024)
    plan = [
        ("media", ["desktop", "web", "assets", "live-image/artwork", "boot/splash", "boot/visual"], MEDIA_EXT),
        ("apps", ["web", "apps", "desktop"], APP_EXT),
        ("docs", ["docs"], DOC_EXT),
        ("workflows", [".github/workflows"], {".yml", ".yaml"}),
        ("catalogues", ["isa", "tools/commands", "userland/commands", "config", "architecture", "include"], {".json", ".sql", ".h", ".hpp", ".c", ".cpp", ".md"}),
    ]
    dest_root = os.path.join(args.iso, "payload")
    shutil.rmtree(dest_root, ignore_errors=True)
    entries, copied, skipped = [], 0, 0
    used = 0
    seen = set()
    for kind, subdirs, exts in plan:
        for sub, path in sorted(collect(args.root, subdirs, exts)):
            rel = os.path.relpath(path, args.root)
            if rel in seen:
                continue
            seen.add(rel)
            size = os.path.getsize(path)
            if used + size > budget:
                skipped += 1
                continue
            out = os.path.join(dest_root, kind, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(path, out)
            entries.append({"kind": kind, "path": rel, "bytes": size, "sha256": sha256(path)})
            used += size
            copied += 1

    manifest = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": copied,
        "skipped_over_budget": skipped,
        "bytes": used,
        "kinds": {},
        "entries": entries,
    }
    for e in entries:
        manifest["kinds"][e["kind"]] = manifest["kinds"].get(e["kind"], 0) + 1
    os.makedirs(dest_root, exist_ok=True)
    with open(os.path.join(dest_root, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    with open(os.path.join(dest_root, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(f"{e['sha256']}  {e['kind']}/{e['path']}\n")
    print(f"payload: {copied} files, {used/1048576:.1f} MiB, kinds={manifest['kinds']}, skipped={skipped}")


if __name__ == "__main__":
    main()
