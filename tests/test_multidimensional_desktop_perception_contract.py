#!/usr/bin/env python3
"""Source-contract checks for the desktop perception integration design."""
import pathlib
import unittest

DOC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "MULTIDIMENSIONAL_DESKTOP_PERCEPTION.md"

class PerceptionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_dimensions_are_not_capped_at_128(self):
        for token in ("129", "256", "512", "1024", "8192"):
            self.assertIn(token, self.text)
        self.assertIn("not a hard maximum", self.text)

    def test_capture_is_opt_in_and_revocable(self):
        self.assertIn("Capture disabled until granted", self.text)
        self.assertIn("permission withdrawal", self.text.lower())
        self.assertIn("lock screen", self.text.lower())

    def test_worker_is_isolated(self):
        self.assertIn("unprivileged", self.text)
        self.assertIn("no kernel pointers", self.text)
        self.assertIn("worker crash", self.text)

    def test_real_vision_tasks_and_inference_are_named(self):
        for token in ("Detection", "Segmentation", "Tracking", "OCR", "ONNX Runtime"):
            self.assertIn(token, self.text)

    def test_release_requires_runtime_evidence(self):
        self.assertIn("real compositor frame paths", self.text)
        self.assertIn("Do not publish a release artifact", self.text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
