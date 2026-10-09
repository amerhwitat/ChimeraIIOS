#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/catalogs/refresh_online_catalogs.py"
spec = importlib.util.spec_from_file_location("refresh_online_catalogs", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class CatalogRefreshTests(unittest.TestCase):
    def test_aliases_include_required_arabic_examples(self):
        self.assertEqual(mod.ARABIC_ALIASES["ls"], "عرض")
        self.assertEqual(mod.ARABIC_ALIASES["cat"], "اقرأ")
        self.assertEqual(mod.ARABIC_ALIASES["git"], "جيت")
        self.assertEqual(mod.ARABIC_ISA_FAMILIES["RISC-V"], "ريسك-في")
        aliases = list(mod.ARABIC_ALIASES.values())
        self.assertEqual(len(aliases), len(set(aliases)))

    def test_aliases_are_unambiguous_for_reverse_lookup(self):
        registry = mod.read_json(mod.ARABIC_FILE, {})
        values = list(registry.get("aliases", {}).values())
        self.assertEqual(len(values), len(set(values)))

    def test_command_names_filter_navigation(self):
        self.assertEqual(mod.candidate_name("Home"), "")
        self.assertEqual(mod.candidate_name("grep"), "grep")

    def test_url_resolution(self):
        self.assertEqual(
            mod.canonical_url("https://example.org/a/index.html", "../grep"),
            "https://example.org/grep",
        )

    def test_tablegen_definitions_are_discovery_candidates_only(self):
        candidates = mod.extract_definition_identifiers("def ADD : Inst;\ndef SUB : Inst;\ndef ADD : Inst;")
        self.assertEqual(candidates, ["ADD", "SUB"])
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("do not establish ISA conformance", source)
        registry = mod.update_arabic_registry({}, [])
        self.assertEqual(registry["arabic_to_canonical"]["عرض"], "ls")


if __name__ == "__main__":
    unittest.main()
