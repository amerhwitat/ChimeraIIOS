#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "cognition"))
from chimera_rnn import Evidence, KnowledgeBus, RecurrentState


class CognitionTests(unittest.TestCase):
    def test_recurrent_state_is_bounded_and_deterministic(self):
        a = RecurrentState(8)
        b = RecurrentState(8)
        self.assertEqual(a.step([1, 2, 3]), b.step([1, 2, 3]))
        self.assertTrue(all(-1.0 <= x <= 1.0 for x in a.state))

    def test_evidence_hash_and_export(self):
        e = Evidence.from_text("https://example.org", "Example", "fact")
        bus = KnowledgeBus()
        bus.add(e)
        self.assertEqual(len(e.content_hash), 64)
        self.assertIn("Example", bus.export())


if __name__ == "__main__":
    unittest.main()
