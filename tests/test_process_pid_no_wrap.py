"""Regression checks for PID allocator identity exhaustion behavior."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kernel" / "core" / "process.cpp"


class ProcessPidNoWrapTests(unittest.TestCase):
    def test_pid_allocator_never_wraps_to_a_reusable_identity(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("next_pid == 0 || next_pid > 0x7FFFFFFFu", source)
        self.assertIn("next_pid = (next_pid == UINT32_MAX) ? 0 : next_pid + 1;", source)
        self.assertNotIn("if (!next_pid) next_pid = 1;", source)

    def test_pid_exhaustion_is_checked_before_slot_is_committed(self):
        source = SOURCE.read_text(encoding="utf-8")
        guard = source.index("if (next_pid == 0 || next_pid > 0x7FFFFFFFu)")
        commit = source.index("slots[i].image = p;", guard)
        self.assertLess(guard, commit)

    def test_registry_initialization_cannot_clear_live_identity_state(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("static bool process_registry_initialized = false;", source)
        guard = source.index("if (process_registry_initialized) return 0;")
        reset = source.index("slots[i] = {};", guard)
        initialized = source.index("process_registry_initialized = true;", reset)
        self.assertLess(guard, reset)
        self.assertLess(reset, initialized)


if __name__ == "__main__":
    unittest.main()
