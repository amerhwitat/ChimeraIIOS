"""Validate curated driver acquisition metadata without downloading drivers."""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "drivers" / "acquisition_sources.json"


def main() -> int:
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    if data.get("schema") != "CHM-DRIVER-SOURCES-1":
        raise SystemExit("unsupported driver source schema")
    for platform, entries in data.items():
        if platform in {"schema", "policy"}:
            continue
        for entry in entries:
            uri = urlparse(entry["url"])
            if uri.scheme != "https" or not uri.hostname:
                raise SystemExit(f"non-HTTPS source: {entry['url']}")
    print("Driver source metadata: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
