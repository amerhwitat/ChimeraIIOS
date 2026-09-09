#!/usr/bin/env python3
"""Red-phase tests for the unified Chimera II help resolver."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "help"))

from help_core import HelpDatabase, HelpDocument, HelpResolver  # noqa: E402


def test_namespace_and_section_resolution():
    db = HelpDatabase()
    db.add(HelpDocument(id="linux:ls:1", namespace="linux", name="ls", section="1", title="ls"))
    db.add(HelpDocument(id="posix:ls:1", namespace="posix", name="ls", section="1", title="ls POSIX"))
    resolver = HelpResolver(db)

    assert resolver.resolve("linux:ls").id == "linux:ls:1"
    assert resolver.resolve("1", "ls").id == "linux:ls:1"


def test_alias_and_search():
    db = HelpDatabase()
    db.add(HelpDocument(id="linux:manual:1", namespace="linux", name="manual", section="1", title="Manual viewer", aliases=["man"]))
    resolver = HelpResolver(db)

    assert resolver.resolve("man").id == "linux:manual:1"
    assert resolver.search("viewer")[0].id == "linux:manual:1"


def test_unknown_page_is_none():
    assert HelpResolver(HelpDatabase()).resolve("does-not-exist") is None


if __name__ == "__main__":
    tests = [test_namespace_and_section_resolution, test_alias_and_search, test_unknown_page_is_none]
    for test in tests:
        test()
    print("help core tests: PASS")
