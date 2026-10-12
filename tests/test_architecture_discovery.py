from __future__ import annotations

import unittest

from tools.architecture_discovery.chimera_discovery import ALLOWED_HOSTS, scan, source_host


class ArchitectureDiscoveryTests(unittest.TestCase):
    def test_rejects_non_https(self):
        with self.assertRaises(ValueError):
            source_host("http://github.com/example")

    def test_rejects_unapproved_host(self):
        with self.assertRaises(ValueError):
            source_host("https://example.invalid/isa")

    def test_allowlist_is_explicit(self):
        self.assertIn("riscv.org", ALLOWED_HOSTS)
        self.assertNotIn("example.invalid", ALLOWED_HOSTS)

    def test_offline_mode_never_fetches_and_marks_candidate_status(self):
        report = scan({"sources": [{"title": "test", "url": "https://github.com/riscv/riscv-isa-manual"}]}, [], False)
        self.assertEqual(report["mode"], "offline")
        self.assertEqual(report["sources"][0]["status"], "not-checked-offline")
        self.assertEqual(report["sources"][0]["candidates"], [])

    def test_catalog_rows_are_not_promoted_to_execution_support(self):
        report = scan({"sources": []}, [], False)
        self.assertEqual(report["compatibility_proposals"], [])
        self.assertIn("never promotes a candidate to supported", report["policy"])


if __name__ == "__main__":
    unittest.main()
