#!/usr/bin/env python3
"""Regression tests for the online catalog merge stage."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("merge_online_catalogs.py")
SPEC = importlib.util.spec_from_file_location("merge_online_catalogs", MODULE_PATH)
MERGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MERGER)


class MergeOnlineCatalogsTests(unittest.TestCase):
    def test_command_references_merge_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = root / "online-command-catalog.json"
            database = root / "ss64-command-catalog.json"
            index.write_text(json.dumps({
                "sources": [{
                    "id": "linux-docs",
                    "platform": "Linux",
                    "url": "https://example.org/commands",
                    "commands": [{"name": "ls", "url": "https://example.org/ls"}]
                }],
                "commands": [{
                    "name": "cat",
                    "platform": "Linux",
                    "source_urls": ["https://example.org/cat"],
                    "arabic_alias": "اقرأ",
                    "translation_status": "curated"
                }]
            }), encoding="utf-8")
            MERGER.COMMAND_INDEX = index
            MERGER.COMMAND_DB = database

            MERGER.merge_commands()
            first = json.loads(database.read_text(encoding="utf-8"))
            linux = first["platforms"]["linux"]["commands"]
            self.assertEqual({row["name"] for row in linux}, {"ls", "cat"})
            self.assertTrue(all(row["provider_status"] == "unverified" for row in linux))

            MERGER.merge_commands()
            second = json.loads(database.read_text(encoding="utf-8"))
            self.assertEqual(len(second["platforms"]["linux"]["commands"]), 2)

    def test_missing_source_index_does_not_overwrite_existing_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = root / "missing.json"
            database = root / "existing.json"
            original = {"platforms": {"linux": {"commands": [{"name": "known"}]}}}
            database.write_text(json.dumps(original), encoding="utf-8")
            MERGER.COMMAND_INDEX = index
            MERGER.COMMAND_DB = database

            MERGER.merge_commands()
            self.assertEqual(json.loads(database.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()
