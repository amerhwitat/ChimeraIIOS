#!/usr/bin/env python3
"""Unified read-only file/directory/media metadata provider for Aurora."""

from __future__ import annotations
import argparse, hashlib, json, mimetypes, os, stat, subprocess
from pathlib import Path

def _iso(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()

def _hash(path: Path, algorithm: str) -> str | None:
    h = hashlib.new(algorithm)
    try:
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()
    except (OSError, ValueError):
        return None

def _mime(path: Path) -> tuple[str, str]:
    guessed, _ = mimetypes.guess_type(path.name, strict=False)
    if guessed:
        return guessed, "filename"
    try:
        p = subprocess.run(["file","--brief","--mime-type",str(path)], text=True,
                           capture_output=True, check=False, timeout=3)
        value = p.stdout.strip()
        if value:
            return value, "content"
    except (OSError, subprocess.SubprocessError):
        pass
    return "application/octet-stream", "unknown"

def _dir_summary(path: Path) -> dict:
    total = files = dirs = links = 0
    try:
        for root, names, filenames in os.walk(path, followlinks=False):
            dirs += len(names)
            files += len(filenames)
            for name in names:
                try:
                    if (Path(root) / name).is_symlink(): links += 1
                except OSError: pass
            for name in filenames:
                try:
                    total += (Path(root) / name).lstat().st_size
                except OSError: pass
    except OSError:
        pass
    return {"recursive_size_bytes": total, "recursive_file_count": files,
            "recursive_directory_count": dirs, "symlink_count": links}

def properties(path: Path, hashes: bool = False) -> dict:
    st = path.lstat()
    mode = stat.filemode(st.st_mode)
    mime, source = _mime(path) if path.is_file() else ("inode/directory", "directory")
    out = {
        "path": str(path.resolve(strict=False)), "name": path.name, "basename": path.stem,
        "extension": path.suffix.lower(), "parent": str(path.parent.resolve(strict=False)),
        "uri": path.resolve(strict=False).as_uri(), "kind": "directory" if path.is_dir() else "file",
        "mime_type": mime, "mime_source": source, "is_regular": path.is_file(),
        "is_directory": path.is_dir(), "is_symlink": path.is_symlink(),
        "is_mountpoint": path.is_mount(), "is_hidden": path.name.startswith("."),
        "size_bytes": st.st_size, "inode": st.st_ino, "device": st.st_dev,
        "link_count": st.st_nlink, "mode": mode, "permissions": oct(stat.S_IMODE(st.st_mode)),
        "owner_uid": st.st_uid, "group_gid": st.st_gid,
        "created": _iso(getattr(st, "st_birthtime", st.st_ctime)),
        "modified": _iso(st.st_mtime), "accessed": _iso(st.st_atime),
        "metadata_changed": _iso(st.st_ctime)
    }
    try:
        import pwd, grp
        out["owner"] = pwd.getpwuid(st.st_uid).pw_name
        out["group"] = grp.getgrgid(st.st_gid).gr_name
    except (ImportError, KeyError):
        pass
    if hashes and path.is_file():
        out["sha256"] = _hash(path, "sha256")
        out["sha512"] = _hash(path, "sha512")
    if path.is_dir():
        out["directory"] = _dir_summary(path)
    return out

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--hash", action="store_true")
    p.add_argument("--pretty", action="store_true")
    a = p.parse_args()
    print(json.dumps(properties(a.path, a.hash), ensure_ascii=False, indent=2 if a.pretty else None))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
