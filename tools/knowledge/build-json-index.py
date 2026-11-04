#!/usr/bin/env python3
"""Build a provenance-preserving, local JSON retrieval index.

Only repository-local allowlisted roots are indexed. This is retrieval preparation,
not model training or a claim that an LLM/RNN/CNN inference runtime is installed.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXTS = {".md", ".txt", ".rst", ".json", ".jsonl", ".yaml", ".yml", ".toml",
        ".ini", ".cfg", ".py", ".sh", ".c", ".cc", ".cpp", ".h", ".hpp",
        ".rs", ".js", ".ts", ".html", ".css", ".xml", ".csv"}
DENY_PARTS = {".git", "build", "dist", "target", "node_modules", ".cache",
              ".venv", "__pycache__", "secrets", "credentials", ".ssh", "private"}
DENY_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}
DENY_NAME_PARTS = ("secret", "credential", "token", "password", "private", "apikey", "api_key")
CHUNK = 1400
OVERLAP = 180
MAX_FILE = 1_000_000
MAX_TOTAL = 100_000_000

def safe_path(raw: str) -> pathlib.Path | None:
    p = (ROOT / raw).resolve()
    try:
        p.relative_to(ROOT)
    except ValueError:
        return None
    return p if p.is_dir() else None

def chunks(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    start = 0
    while start < len(text):
        end = min(len(text), start + CHUNK)
        if end < len(text):
            boundary = text.rfind("\n", start + CHUNK // 2, end)
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = max(start + 1, end - OVERLAP)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", action="append", default=[])
    args = ap.parse_args()
    raw_roots = args.source or os.environ.get("CHIMERA_KNOWLEDGE_SOURCES", "").split(os.pathsep)
    roots = [safe_path(x.strip()) for x in raw_roots if x.strip()]
    if not roots:
        roots = [safe_path(x) for x in ("docs", "desktop", "applications",
                 "appcenter/catalog", "isa", "config", "sdk", "tools")]
    roots = [p for p in roots if p]
    seen, docs, total = set(), [], 0
    for base in roots:
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in EXTS:
                continue
            rel = path.relative_to(ROOT)
            if any(part.lower() in DENY_PARTS for part in rel.parts) or path.name.lower() in DENY_NAMES or any(x in path.name.lower() for x in DENY_NAME_PARTS):
                continue
            try:
                size = path.stat().st_size
                if size <= 0 or size > MAX_FILE or total + size > MAX_TOTAL:
                    continue
                data = path.read_bytes()
                content = data.decode("utf-8")
            except (OSError, UnicodeError):
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen:
                continue
            seen.add(digest); total += size
            parts = list(chunks(content))
            docs.append({"source": rel.as_posix(), "sha256": digest,
                         "size_bytes": size, "chunks": [
                             {"chunk_id": i, "text": part} for i, part in enumerate(parts)]})
    payload = {"schema": "chimera-local-knowledge-json-v1",
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "repository": ROOT.name, "scope": "repository-local allowlisted text resources only",
               "training": False, "inference_runtime": "not-provided-by-indexer",
               "privacy": "No home-directory, credential, secret, or arbitrary host-file ingestion.",
               "limits": {"max_file_bytes": MAX_FILE, "max_total_bytes": MAX_TOTAL,
                          "chunk_chars": CHUNK, "overlap_chars": OVERLAP},
               "summary": {"documents": len(docs), "bytes_indexed": total,
                           "chunks": sum(len(d["chunks"]) for d in docs)},
               "documents": docs}
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(json.dumps(payload["summary"], sort_keys=True))

if __name__ == "__main__":
    main()
