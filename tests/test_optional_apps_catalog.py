"""Regression tests for optional app catalog validation."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_optional_apps_catalog.py"
SPEC = importlib.util.spec_from_file_location("check_optional_apps_catalog", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OptionalAppCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.catalog = json.loads(MODULE.CATALOG.read_text(encoding="utf-8"))

    def test_current_catalog_passes(self):
        self.assertEqual(MODULE.validate(self.catalog), [])

    def test_duplicate_id_is_rejected(self):
        data = dict(self.catalog)
        data["apps"] = [dict(app) for app in self.catalog["apps"]]
        data["apps"][1]["id"] = data["apps"][0]["id"]
        self.assertTrue(any("duplicates" in e for e in MODULE.validate(data)))

    def test_installed_by_default_is_rejected(self):
        data = dict(self.catalog)
        data["apps"] = [dict(app) for app in self.catalog["apps"]]
        data["apps"][0]["default_installed"] = True
        self.assertTrue(any("default_installed must be false" in e for e in MODULE.validate(data)))

    def test_non_https_upstream_is_rejected(self):
        data = dict(self.catalog)
        data["apps"] = [dict(app) for app in self.catalog["apps"]]
        data["apps"][0]["upstream"] = "http://example.com"
        self.assertTrue(any("must be an HTTPS URL" in e for e in MODULE.validate(data)))

    def test_malformed_platform_shape_is_rejected_without_crashing(self):
        data = dict(self.catalog)
        data["platforms"] = [["nested"]]
        self.assertTrue(any("unsupported platform" in e for e in MODULE.validate(data)))

    def test_unknown_platform_is_rejected(self):
        data = dict(self.catalog)
        data["apps"] = [dict(app) for app in self.catalog["apps"]]
        data["apps"][0]["platforms"] = ["ChimeraIIOS"]
        self.assertTrue(any("unsupported platform" in e for e in MODULE.validate(data)))


if __name__ == "__main__":
    unittest.main()
