#!/usr/bin/env python3
"""Offline BM25 retrieval console for Chimera/Octavian JSON knowledge indexes.

This is a source-citing retrieval tool, not a neural model or generative LLM.
"""
from __future__ import annotations
import argparse, json, math, pathlib, re, sys

TOKEN = re.compile(r"[a-z0-9_+-]{2,}", re.I)

def terms(text: str):
    return TOKEN.findall(text.lower())

def retrieve(payload, query, limit=5):
    q = terms(query)
    docs = []
    df = {}
    total_len = 0
    for source in payload.get("documents", []):
        for chunk in source.get("chunks", []):
            words = terms(chunk.get("text", ""))
            if not words:
                continue
            freq = {}
            for word in words:
                freq[word] = freq.get(word, 0) + 1
            docs.append((source, chunk, freq, len(words)))
            total_len += len(words)
            for word in set(freq):
                df[word] = df.get(word, 0) + 1
    if not docs or not q:
        return []
    avg = total_len / len(docs)
    n = len(docs)
    scored = []
    for source, chunk, freq, length in docs:
        score = 0.0
        for word in q:
            tf = freq.get(word, 0)
            if not tf:
                continue
            idf = math.log(1.0 + (n - df.get(word, 0) + 0.5) / (df.get(word, 0) + 0.5))
            denom = tf + 1.5 * (1.0 - 0.75 + 0.75 * length / max(avg, 1.0))
            score += idf * tf * 2.5 / denom
        if score:
            scored.append((score, source, chunk))
    return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--query")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    path = pathlib.Path(args.index)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot load knowledge database: {exc}", file=sys.stderr)
        return 2
    def answer(query):
        results = retrieve(payload, query, max(1, min(args.limit, 20)))
        if not results:
            print("No matching indexed evidence. Try different terms.")
            return
        for rank, (score, source, chunk) in enumerate(results, 1):
            print(f"\n[{rank}] {source.get('source','unknown')}  score={score:.3f}")
            print(f"    sha256={source.get('sha256','')}")
            print(chunk.get("text", "").strip())
        print("\nRetrieval only: results are source excerpts, not model-generated conclusions.")
    if args.query:
        answer(args.query)
        return 0
    print("Local Knowledge Chat — BM25 retrieval (no network/model inference). Type /quit to exit.")
    while True:
        try:
            query = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if query.lower() in {"/quit", "/exit"}:
            break
        if query:
            answer(query)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
