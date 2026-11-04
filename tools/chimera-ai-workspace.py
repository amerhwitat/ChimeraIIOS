#!/usr/bin/env python3
"""Local, opt-in resource index and model-runtime probe for Chimera AI Workspace.

The index is metadata-only by default. Text extraction requires --include-text and
only applies to explicitly supplied roots. Nothing is uploaded and model weights
are never modified by this tool.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "CHIMERA-AI-RESOURCE-DB-1"
SKIP_DIRS = {".git", ".hg", ".svn", ".cache", ".venv", "venv", "node_modules",
             "__pycache__", ".pytest_cache", ".ssh", ".gnupg", "browser", "profiles"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
                   "credentials", "secrets", "secrets.json", "token", "tokens.json",
                   "passwords", "password-store"}
TEXT_EXTS = {".txt", ".md", ".rst", ".py", ".c", ".h", ".cpp", ".hpp", ".rs",
             ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".ini", ".sh",
             ".xml", ".html", ".css", ".sql", ".cmake"}
MAX_TEXT = 64 * 1024

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def skipped(path: Path) -> bool:
    # os.walk prunes hidden directories before descending; this function handles
    # hidden leaf files and sensitive names without rejecting an explicitly
    # selected root merely because one of its parent directories is hidden.
    name = path.name.casefold()
    if name.startswith(".") or name in SENSITIVE_NAMES:
        return True
    if name.startswith(("id_rsa", "id_ed25519")):
        return True
    if name in {".netrc", ".npmrc", ".pypirc", ".git-credentials",
                "authorized_keys", "known_hosts"}:
        return True
    if name.endswith((".pem", ".key", ".p12", ".pfx", ".kdbx", ".secret")):
        return True
    if name in {"credentials", "secrets", "password-store", "private"}:
        return True
    return False

def probe() -> dict:
    commands = {}
    for name in ("llama-cli", "llama-server", "ollama", "python3", "clang", "gcc"):
        p = shutil.which(name)
        version = ""
        if p:
            try:
                r = subprocess.run([p, "--version"], text=True, capture_output=True, timeout=5)
                version = (r.stdout or r.stderr).strip().splitlines()[0][:160]
            except Exception:
                pass
        commands[name] = {"available": bool(p), "path": p or "", "version": version}
    modules = {}
    for name in ("torch", "onnxruntime", "transformers", "tensorflow", "numpy"):
        try:
            m = __import__(name)
            modules[name] = {"available": True, "version": str(getattr(m, "__version__", ""))}
        except Exception:
            modules[name] = {"available": False, "version": ""}
    return {"commands": commands, "python_modules": modules}

def scan(args) -> int:
    roots = [Path(x).expanduser().resolve() for x in args.root]
    for root in roots:
        if not root.is_dir():
            raise SystemExit(f"resource root is not a directory: {root}")
    rows, seen = [], set()
    for root in roots:
        for base, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d.casefold() not in SKIP_DIRS and not d.startswith("."))
            for name in sorted(files):
                p = Path(base) / name
                try:
                    if skipped(p) or p.is_symlink() or not p.is_file():
                        continue
                    st = p.stat()
                    if st.st_size > args.max_file_mb * 1024 * 1024:
                        continue
                    rel = str(p.relative_to(root))
                    identity = str(p)
                    if identity in seen:
                        continue
                    seen.add(identity)
                    item = {"root": str(root), "path": rel, "size": st.st_size,
                            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                            "sha256": digest(p), "kind": p.suffix.lower().lstrip(".") or "file"}
                    if args.include_text and p.suffix.lower() in TEXT_EXTS and st.st_size <= MAX_TEXT:
                        try:
                            item["text"] = p.read_text(encoding="utf-8")[:MAX_TEXT]
                        except (UnicodeError, OSError):
                            pass
                    rows.append(item)
                except (OSError, PermissionError):
                    continue
    db = {"schema": SCHEMA, "generated_utc": datetime.now(timezone.utc).isoformat(),
          "host": {"platform": platform.platform(), "machine": platform.machine()},
          "policy": {"metadata_only_default": True, "text_extraction_enabled": bool(args.include_text),
                     "uploaded": False, "excluded_sensitive_paths": True},
          "roots": [str(x) for x in roots], "resource_count": len(rows), "resources": rows}
    dest = Path(args.database).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(dest)
    print(f"indexed {len(rows)} resources -> {dest}")
    return 0

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan", help="index explicitly selected local resource roots")
    s.add_argument("--root", action="append", required=True, help="root directory; repeat as needed")
    s.add_argument("--database", default="~/.local/share/chimera-ai/resources.json")
    s.add_argument("--include-text", action="store_true", help="opt in to storing small text-file contents")
    s.add_argument("--max-file-mb", type=int, default=32)
    s.set_defaults(func=scan)
    sub.add_parser("status", help="probe available local LLM/CNN/RNN runtime components").set_defaults(
        func=lambda _: (print(json.dumps(probe(), indent=2)) or 0))
    args = p.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
