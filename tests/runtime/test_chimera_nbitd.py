import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "runtime" / "chimera-nbitd.py"
SPEC = importlib.util.spec_from_file_location("chimera_nbitd", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class NBitDaemonTests(unittest.TestCase):
    def test_info_is_explicitly_software_only(self):
        result = MODULE.handle_request({"op": "info", "width": 8192})
        self.assertTrue(result["ok"])
        self.assertFalse(result["hardware_native"])
        self.assertFalse(result["guest_isa_execution"])
        self.assertEqual(result["execution"], "software-reference")

    def test_calculation_wraps_and_returns_hex(self):
        result = MODULE.handle_request({
            "op": "calculate", "operation": "add",
            "lhs": 255, "rhs": 1, "width": 8,
        })
        self.assertEqual(result["result"], "0x0")
        self.assertFalse(result["hardware_native"])

    def test_rejects_invalid_width_and_operation(self):
        with self.assertRaises(ValueError):
            MODULE.handle_request({"op": "info", "width": 7})
        with self.assertRaises(ValueError):
            MODULE.handle_request({
                "op": "calculate", "operation": "execute-shell",
                "lhs": 1, "rhs": 1, "width": 32,
            })

    def test_rejects_non_object_request(self):
        with self.assertRaises(ValueError):
            MODULE.handle_request(["calculate"])


if __name__ == "__main__":
    unittest.main()
