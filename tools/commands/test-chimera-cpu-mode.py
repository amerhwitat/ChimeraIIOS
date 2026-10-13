#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("chimera-cpu-mode.py")
SPEC = importlib.util.spec_from_file_location("chimera_cpu_mode", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class CpuModeTests(unittest.TestCase):
    def test_real_profile_disables_dpmi(self):
        self.assertIn("dpmi=false", MODULE.dosbox_config("real", False))

    def test_protected_capable_profile_enables_dpmi(self):
        self.assertIn("dpmi=true", MODULE.dosbox_config("protected", False))

    def test_host_cpu_list_is_nonempty(self):
        self.assertGreaterEqual(len(MODULE.host_cpus()), 1)

if __name__ == "__main__":
    unittest.main()
