import base64
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
registryd = load("registryd", "services/registry/registryd.py")
hive_tool = ROOT / "tools/registry/registry_hive.py"

class RegistryServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        registryd.ROOT = pathlib.Path(self.temp.name)
        registryd.TOOL = hive_tool
        for name in registryd.HIVES:
            source = json.loads((ROOT / "system/registry" / (name + ".defaults.json")).read_text())
            (registryd.ROOT / (name + ".json")).write_text(json.dumps(source))

    def tearDown(self):
        self.temp.cleanup()

    def test_read_hive(self):
        result = registryd._handle({"op": "read", "hive": "environment"}, False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["generation"], 1)

    def test_generation_checked_write_and_binary_commit(self):
        result = registryd._handle({"op": "set", "hive": "environment",
            "path": "environment.locale", "type": "string",
            "value": "en_GB.UTF-8", "generation": 1}, True)
        self.assertEqual(result["generation"], 2)
        self.assertTrue((registryd.ROOT / "environment.hive").is_file())
        reread = registryd._handle({"op": "read", "hive": "environment"}, False)
        self.assertEqual(reread["generation"], 2)
        self.assertEqual(next(x["value"] for x in reread["entries"] if x["path"] == "environment.locale"), "en_GB.UTF-8")

    def test_binary_hive_must_match_source(self):
        registryd._handle({"op": "read", "hive": "environment"}, False)
        (registryd.ROOT / "environment.hive").write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            registryd._handle({"op": "read", "hive": "environment"}, False)

    def test_stale_and_boolean_generations_rejected(self):
        for generation in (0, True):
            with self.assertRaises(RuntimeError):
                registryd._handle({"op": "set", "hive": "environment",
                    "path": "environment.locale", "type": "string",
                    "value": "x", "generation": generation}, True)

    def test_protected_and_cross_hive_keys_rejected(self):
        for hive, key in (("machine", "cpu.selection.policy"),
                          ("machine", "machine.identity.profile"),
                          ("kernel", "kernel.smp.requested"),
                          ("environment", "kernel.debug.log_level"),
                          ("environment", "security.foo")):
            with self.assertRaises((PermissionError, ValueError)):
                registryd._handle({"op": "set", "hive": hive, "path": key,
                    "type": "string", "value": "bad", "generation": 1}, True)

    def test_prepared_transaction_replays_source_and_binary(self):
        obj = json.loads((registryd.ROOT / "environment.json").read_text())
        obj["generation"] = 2
        source = (json.dumps(obj, indent=2) + "\n").encode()
        import subprocess, sys
        with tempfile.TemporaryDirectory() as work:
            inp = pathlib.Path(work) / "source.json"
            out = pathlib.Path(work) / "environment.hive"
            inp.write_bytes(source)
            subprocess.run([sys.executable, str(hive_tool), "build", "--input", str(inp), "--output", str(out)], check=True)
            binary = out.read_bytes()
        journal = {"hive": "environment", "source": base64.b64encode(source).decode(),
                   "binary": base64.b64encode(binary).decode()}
        (registryd.ROOT / "environment.transaction.json").write_text(json.dumps(journal))
        registryd._recover("environment")
        self.assertFalse((registryd.ROOT / "environment.transaction.json").exists())
        self.assertEqual(json.loads((registryd.ROOT / "environment.json").read_text())["generation"], 2)
        self.assertEqual((registryd.ROOT / "environment.hive").read_bytes(), binary)

if __name__ == "__main__":
    unittest.main()
