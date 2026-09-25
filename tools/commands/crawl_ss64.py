#!/usr/bin/env python3
"""Build a machine-readable SS64 command catalog for Chimera II OS.

The crawler records command names, platform/category, and SS64 source URLs.
It intentionally does NOT copy SS64 page prose. SS64 publishes A-Z command
indexes for Linux/Bash and other command-line environments; this tool follows
those indexes and command-reference pages to populate the local JSON registry.

Usage:
  python3 tools/commands/crawl_ss64.py \
      --output system/commands/ss64-command-catalog.json \
      --max-pages 3000
"""
from __future__ import annotations

import argparse
import html.parser
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = "https://ss64.com/"
INDEXES = {
    "linux_bash": "https://ss64.com/bash/",
    "macos": "https://ss64.com/mac/",
    "windows_cmd": "https://ss64.com/nt/",
    "powershell": "https://ss64.com/ps/",
    "vbscript": "https://ss64.com/vb/",
    "sql_server": "https://ss64.com/sql/",
    "access": "https://ss64.com/access/",
    "tools": "https://ss64.com/tools/",
}
DEFAULT_MAX_PAGES = 3000
DEFAULT_DELAY = 0.05
USER_AGENT = "ChimeraIIOS-SS64-Catalog/3.1 (+https://github.com/amerhwitat/ChimeraIIOS)"


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._inside_a = False
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self._inside_a = True
            self._href = dict(attrs).get("href", "")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._inside_a:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._inside_a:
            text = " ".join("".join(self._text).split())
            self.links.append((text, self._href))
            self._inside_a = False
            self._href = ""
            self._text = []


def fetch(url: str, timeout: float, retries: int) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2.0, 0.25 * (attempt + 1)))
    raise RuntimeError(f"unable to fetch {url}: {last_error}")


def clean_label(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"\s*[•▫]+\s*$", "", value).strip()
    return value


def looks_like_command(label: str, url: str) -> bool:
    if not label or len(label) > 160:
        return False
    if len(label) == 1 and label.isalpha():
        return False
    if label in {
        "Home", "Search", "Contact", "About", "Donate", "Examples", "Syntax",
        "Related", "Next", "Previous", "Back", "Top", "Index", "More",
    }:
        return False
    if label.startswith(("http://", "https://", "mailto:")):
        return False
    path = urllib.parse.urlparse(url).path.lower()
    if not path.endswith((".html", ".htm", "/")):
        return False
    return bool(re.search(r"[A-Za-z0-9_$?&./+:-]", label))


def command_record(label: str, url: str, platform: str) -> dict | None:
    label = clean_label(label)
    if not looks_like_command(label, url):
        return None
    return {
        "name": label,
        "platform": platform,
        "source": url,
    }


def crawl_index(
    seed: str,
    platform: str,
    max_pages: int,
    timeout: float,
    retries: int,
    delay: float,
) -> tuple[list[dict], int, int]:
    seed_url = urllib.parse.urlparse(seed)
    host = seed_url.netloc
    prefix = seed_url.path.rstrip("/") + "/"
    queue = [seed]
    queued = {seed}
    seen: set[str] = set()
    entries: dict[tuple[str, str, str], dict] = {}
    pages = 0
    failures = 0

    while queue and pages < max_pages:
        url = queue.pop(0)
        queued.discard(url)
        if url in seen:
            continue

        parsed = urllib.parse.urlparse(url)
        if parsed.netloc != host or not parsed.path.startswith(prefix):
            continue

        seen.add(url)
        pages += 1
        try:
            html = fetch(url, timeout, retries)
        except Exception as exc:
            failures += 1
            print(f"[WARN] {platform}: {url}: {exc}")
            continue

        parser = LinkParser()
        parser.feed(html)

        for label, href in parser.links:
            if not href or href.startswith(("#", "javascript:", "mailto:")):
                continue
            absolute = urllib.parse.urljoin(url, href).split("#", 1)[0]
            target = urllib.parse.urlparse(absolute)

            if target.netloc != host or not target.path.startswith(prefix):
                continue

            if absolute not in seen and absolute not in queued:
                queue.append(absolute)
                queued.add(absolute)

            item = command_record(label, absolute, platform)
            if item:
                key = (item["name"].casefold(), item["platform"], item["source"])
                entries[key] = item

        if delay > 0:
            time.sleep(delay)

    return (
        sorted(entries.values(), key=lambda x: (x["name"].casefold(), x["source"])),
        pages,
        failures,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="system/commands/ss64-command-catalog.json",
        help="destination JSON file",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help="maximum pages to crawl per SS64 section",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument(
        "--platforms",
        nargs="*",
        choices=sorted(INDEXES),
        help="optional subset; defaults to all configured SS64 sections",
    )
    args = parser.parse_args()

    max_pages = max(1, args.max_pages)
    selected = args.platforms or list(INDEXES)

    catalog = {
        "schema_version": "3.1",
        "product": "Chimera II OS",
        "source": "SS64",
        "source_index": "https://ss64.com/",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy": (
            "Command names, classifications and source URLs only; "
            "SS64 page prose is not redistributed."
        ),
        "platforms": {},
    }

    total = 0
    for platform in selected:
        entries, pages, failures = crawl_index(
            INDEXES[platform],
            platform,
            max_pages,
            args.timeout,
            max(0, args.retries),
            max(0.0, args.delay),
        )
        catalog["platforms"][platform] = {
            "index": INDEXES[platform],
            "pages_crawled": pages,
            "fetch_failures": failures,
            "command_count": len(entries),
            "commands": entries,
        }
        total += len(entries)
        print(
            f"{platform}: {len(entries)} command links across "
            f"{pages} pages ({failures} fetch failures)"
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output} with {total} command entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
