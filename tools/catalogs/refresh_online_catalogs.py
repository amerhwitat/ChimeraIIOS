#!/usr/bin/env python3
"""Refresh source-backed ISA and OS-command indexes for Chimera II OS.

Only fetches public, explicitly listed sources; uses timeouts and size limits;
records URLs, timestamps, SHA-256 hashes and identifiers, not vendor manuals or
source prose. Network refresh is opt-in so reproducible/offline ISO builds work.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
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
SOURCES_FILE = ROOT / "data/isa/online-source-catalog.json"
ISA_OUT = ROOT / "data/isa/online-isa-index.json"
COMMANDS_OUT = ROOT / "system/commands/online-command-catalog.json"
ARABIC_FILE = ROOT / "system/commands/chimera-arabic.json"
USER_AGENT = "ChimeraIIOS-CatalogIndexer/1.0 (+https://github.com/amerhwitat/ChimeraIIOS)"
TIMEOUT_SECONDS = 18
MAX_BYTES = 4 * 1024 * 1024

# Curated semantic Arabic aliases. Unknown commands are deliberately marked
# untranslated instead of generating misleading or unsafe automatic translations.
ARABIC_ALIASES = {
    "ls":"عرض", "dir":"مجلد", "cd":"انتقل", "pwd":"المسار",
    "cp":"نسخ", "copy":"انسخ", "mv":"نقل", "move":"انقل",
    "rm":"احذف", "del":"احذف", "mkdir":"أنشئ_مجلد", "rmdir":"احذف_مجلد",
    "cat":"اقرأ", "less":"تصفح", "more":"المزيد", "head":"بداية",
    "tail":"نهاية", "grep":"ابحث_نصي", "find":"ابحث", "locate":"اعثر",
    "sort":"رتب", "uniq":"أزل_التكرار", "wc":"عد", "echo":"اطبع",
    "printf":"اطبع_منسق", "clear":"امسح", "history":"السجل",
    "man":"الدليل", "help":"مساعدة", "which":"أين", "whereis":"مكان",
    "ps":"العمليات", "top":"راقب", "kill":"أوقف_عملية", "killall":"أوقف_الكل",
    "df":"مساحة_الأقراص", "du":"استخدام_المساحة", "free":"الذاكرة",
    "mount":"ضم", "umount":"افصل", "chmod":"غيّر_الصلاحيات",
    "chown":"غيّر_المالك", "id":"الهوية", "whoami":"من_أنا",
    "hostname":"اسم_المضيف", "uname":"معلومات_النظام", "date":"التاريخ",
    "uptime":"مدة_التشغيل", "reboot":"أعد_التشغيل", "shutdown":"أوقف_النظام",
    "systemctl":"خدمات_النظام", "ip":"الشبكة", "ping":"اختبر_الاتصال",
    "curl":"طلبات_ويب", "wget":"نزّل", "ssh":"اتصال_آمن", "scp":"نسخ_آمن",
    "tar":"أرشفة", "gzip":"ضغط", "unzip":"فك_الضغط", "nano":"محرر_نانو",
    "git":"جيت", "make":"ابنِ", "cmake":"هيّئ_البناء", "python3":"بايثون",
    "gcc":"مترجم_C", "g++":"مترجم_C++", "docker":"دوكر", "apt":"الحزم",
    "apt-get":"إدارة_الحزم", "dnf":"إدارة_الحزم", "pacman":"مدير_الحزم",
    "mountpoint":"نقطة_الضم", "lsblk":"الأقراص_والكتل", "lscpu":"معلومات_المعالج",
    "lspci":"أجهزة_PCI", "lsusb":"أجهزة_USB", "dmesg":"رسائل_النواة",
    "journalctl":"سجل_النظام", "systemd-analyze":"تحليل_الإقلاع",
    "sqlite3":"قاعدة_SQLite", "psql":"قاعدة_PostgreSQL", "mysql":"قاعدة_MySQL",
    "sqlite":"قاعدة_SQLite", "sql":"استعلام_SQL",
}
ARABIC_GLOSSARY = {
    "add":"جمع", "subtract":"طرح", "multiply":"ضرب", "divide":"قسمة",
    "load":"تحميل", "store":"تخزين", "branch":"قفز_شرطي", "jump":"قفز",
    "compare":"مقارنة", "move":"نقل", "shift":"إزاحة", "rotate":"تدوير",
    "logical":"منطقي", "arithmetic":"حسابي", "register":"مسجل",
    "memory":"ذاكرة", "privileged":"مميّز", "atomic":"ذرّي",
    "floating-point":"فاصلة_عائمة", "vector":"متجه", "system":"نظام",
    "interrupt":"مقاطعة", "exception":"استثناء", "synchronize":"مزامنة",
    "instruction":"تعليمة", "extension":"امتداد", "unknown":"غير_مترجم",
}


class AnchorParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.href: str | None = None
        self.parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            label = " ".join(" ".join(self.parts).split())
            if label and self.href:
                self.anchors.append((label, self.href))
            self.href = None
            self.parts = []


def fetch(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"source exceeds {MAX_BYTES} byte safety limit")
        return raw, response.headers.get_content_type()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def canonical_url(base: str, href: str) -> str:
    from urllib.parse import urljoin, urlparse, urlunparse
    absolute = urljoin(base, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return ""
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def candidate_name(label: str) -> str:
    label = label.strip()
    if len(label) > 80 or not re.search(r"[A-Za-z0-9]", label):
        return ""
    if re.search(r"(?i)(home|next|previous|contents|index|download|github|search|privacy|terms|contact|license|copyright)", label):
        return ""
    return re.sub(r"\s+", " ", label)


def extract_definition_identifiers(text: str) -> list[str]:
    """Extract candidate TableGen definition IDs, not architectural mnemonics."""
    return sorted(set(re.findall(r"(?m)^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)))


def update_arabic_registry(existing: dict[str, Any], commands: list[dict[str, Any]]) -> dict[str, Any]:
    aliases = existing.setdefault("aliases", {})
    reverse = existing.setdefault("arabic_to_canonical", {})
    # Merge only curated aliases; do not overwrite a pre-existing Arabic name
    # assigned to a different command without an explicit human decision.
    for canonical, arabic in ARABIC_ALIASES.items():
        aliases[canonical] = arabic
        reverse[arabic] = canonical
    existing["schema_version"] = str(existing.get("schema_version", "1.1"))
    existing["language"] = "ar"
    existing["direction"] = "rtl"
    existing["description"] = "Curated Arabic command aliases for Chimera II OS, POSIX, Linux, macOS, Windows and development tools."
    existing["catalog_refresh"] = {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "Only curated semantic aliases are executable. Untranslated online commands remain canonical and are labeled untranslated."
    }
    return existing


def refresh() -> int:
    source_doc = read_json(SOURCES_FILE, {})
    if not source_doc:
        raise SystemExit(f"Missing or invalid source catalog: {SOURCES_FILE}")
    timestamp = datetime.now(timezone.utc).isoformat()
    isa_results: list[dict[str, Any]] = []
    command_results: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, str]] = []

    for source in source_doc.get("isa_sources", []):
        url = source["url"]
        row: dict[str, Any] = {**source, "checked_utc": timestamp, "status": "unavailable"}
        try:
            raw, content_type = fetch(url)
            text = raw.decode("utf-8", errors="replace")
            # TableGen 'def' identifiers are useful source-discovery hints, not
            # asserted architectural mnemonics or proof of decoder/executor support.
            defs = extract_definition_identifiers(text) if "tablegen" in source["id"] else []
            row.update({
                "status": "ok",
                "http_content_type": content_type,
                "bytes_read": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "definition_identifiers": defs,
                "definition_identifier_count": len(defs),
                "coverage_note": "Source definitions are discovery candidates only; they do not establish ISA conformance or runtime support."
            })
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            row["error"] = str(exc)
            failures.append({"source": source["id"], "error": str(exc)})
        isa_results.append(row)

    for source in source_doc.get("command_sources", []):
        url = source["url"]
        row = {**source, "checked_utc": timestamp, "status": "unavailable", "commands": []}
        try:
            raw, content_type = fetch(url)
            page = raw.decode("utf-8", errors="replace")
            parser = AnchorParser()
            if "html" in content_type or "<html" in page[:500].lower():
                parser.feed(page)
                entries: dict[str, dict[str, str]] = {}
                for label, href in parser.anchors:
                    name = candidate_name(label)
                    link = canonical_url(url, href)
                    if not name or not link:
                        continue
                    # Avoid capturing unrelated cross-site links from large docs.
                    from urllib.parse import urlparse
                    host = urlparse(link).netloc.lower()
                    source_host = urlparse(url).netloc.lower()
                    if source["id"].startswith("ss64") and not host.endswith("ss64.com"):
                        continue
                    if source["id"] == "windows-commands" and not host.endswith("learn.microsoft.com"):
                        continue
                    key = name.casefold()
                    entries.setdefault(key, {"name": name, "url": link})
                row["commands"] = sorted(entries.values(), key=lambda item: item["name"].casefold())
            row.update({"status": "ok", "http_content_type": content_type, "bytes_read": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            row["error"] = str(exc)
            failures.append({"source": source["id"], "error": str(exc)})
        command_results[source["id"]] = row

    # Combine names across platforms while preserving per-source URLs.
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for source_id, source_row in command_results.items():
        for item in source_row.get("commands", []):
            name = item["name"]
            key = (source_row["platform"], name.casefold())
            merged.setdefault(key, {
                "name": name,
                "platform": source_row["platform"],
                "source_urls": [],
                "arabic_alias": ARABIC_ALIASES.get(name.casefold()),
                "translation_status": "curated" if name.casefold() in ARABIC_ALIASES else "untranslated"
            })["source_urls"].append(item["url"])

    entries = sorted(merged.values(), key=lambda item: (item["platform"], item["name"].casefold()))
    previous = read_json(COMMANDS_OUT, {})
    successful_isa = sum(1 for item in isa_results if item["status"] == "ok")
    successful_commands = sum(1 for item in command_results.values() if item["status"] == "ok")
    if successful_isa == 0:
        print("Warning: no ISA sources reachable; preserving any existing ISA index.", file=sys.stderr)
    if successful_commands == 0:
        print("Warning: no command indexes reachable; preserving existing command catalog and Arabic registry.", file=sys.stderr)
    command_doc = {
        "schema_version": "1.0",
        "generated_utc": timestamp,
        "source_policy": "Names, URLs, source hashes and curated Arabic aliases only; no copied reference prose.",
        "sources": list(command_results.values()),
        "command_count": len(entries),
        "curated_arabic_alias_count": sum(1 for item in entries if item["arabic_alias"]),
        "untranslated_count": sum(1 for item in entries if not item["arabic_alias"]),
        "commands": entries
    }
    isa_doc = {
        "schema_version": "1.0",
        "generated_utc": timestamp,
        "source_policy": "Source metadata and hashes plus TableGen definition identifiers only. Not an exhaustive instruction list and not a conformance claim.",
        "sources": isa_results,
        "successful_source_count": sum(1 for item in isa_results if item["status"] == "ok"),
        "unavailable_source_count": sum(1 for item in isa_results if item["status"] != "ok"),
        "candidate_definition_count": sum(item.get("definition_identifier_count", 0) for item in isa_results)
    }
    arabic = update_arabic_registry(read_json(ARABIC_FILE, {}), entries)
    if successful_isa:
        write_json(ISA_OUT, isa_doc)
    if successful_commands:
        write_json(COMMANDS_OUT, command_doc)
        write_json(ARABIC_FILE, arabic)
    print(f"ISA sources: {isa_doc['successful_source_count']}/{len(isa_results)} fetched; candidate TableGen definitions={isa_doc['candidate_definition_count']}")
    print(f"Command catalog: {len(entries)} names; curated Arabic aliases={command_doc['curated_arabic_alias_count']}; untranslated={command_doc['untranslated_count']}")
    if failures:
        print(f"Warning: {len(failures)} sources were unavailable; see the generated catalog for errors.", file=sys.stderr)
    return 0


def self_test() -> int:
    assert candidate_name("ADD") == "ADD"
    assert candidate_name("Home") == ""
    assert canonical_url("https://example.org/a/index.html", "../cmd") == "https://example.org/cmd"
    assert ARABIC_ALIASES["ls"] == "عرض"
    assert ARABIC_ALIASES["cat"] == "اقرأ"
    parser = AnchorParser()
    parser.feed('<a href="/commands/ls">ls</a><a href="/home">Home</a>')
    assert parser.anchors == [("ls", "/commands/ls"), ("Home", "/home")]
    print("online catalog parser self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run deterministic tests without network access")
    parser.add_argument("--refresh", action="store_true", help="fetch configured public sources and update indexes")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.refresh:
        return refresh()
    parser.error("choose --self-test or --refresh")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
