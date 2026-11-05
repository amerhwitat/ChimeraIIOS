import base64
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
import contextlib
import io
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

registryd = load_module("chimera_registryd", ROOT / "services/registry/registryd.py")
smb = load_module("chimera_smb_browse", ROOT / "services/network/smb-browse.py")
storage = load_module("chimera_mount_image", ROOT / "services/storage/mount-image.py")
directory = load_module("chimera_directoryctl", ROOT / "services/network/directoryctl.py")

class RegistryServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        registryd.ROOT = pathlib.Path(self.tmp.name)
        registryd.TOOL = ROOT / "tools/registry/registry_hive.py"
        self.data = {
            "schema_version": 1, "hive": "environment", "generation": 7,
            "entries": [{"path": "environment.locale", "type": "string", "value": "en_US.UTF-8"}]
        }
        registryd.ROOT.mkdir(parents=True, exist_ok=True)
        (registryd.ROOT / "environment.json").write_text(json.dumps(self.data))
        (registryd.ROOT / "machine.json").write_text(json.dumps({
            "schema_version": 1, "hive": "machine", "generation": 1,
            "entries": [{"path": "cpu.selection.policy", "type": "string", "value": "auto"}]
        }))
        (registryd.ROOT / "kernel.json").write_text(json.dumps({
            "schema_version": 1, "hive": "kernel", "generation": 1, "entries": []
        }))

    def tearDown(self):
        self.tmp.cleanup()

    def test_generation_checked_write_builds_valid_hive(self):
        result = registryd._handle({
            "op": "set", "hive": "environment", "path": "environment.locale",
            "type": "string", "value": "ar_JO.UTF-8", "generation": 7
        }, True)
        self.assertEqual(result["generation"], 8)
        self.assertFalse((registryd.ROOT / "environment.transaction.json").exists())
        verified = subprocess.run(
            ["python3", str(registryd.TOOL), "verify", str(registryd.ROOT / "environment.hive")],
            capture_output=True, text=True, check=True
        )
        self.assertIn('"generation": 8', verified.stdout)
        saved = json.loads((registryd.ROOT / "environment.json").read_text())
        self.assertEqual(saved["entries"][0]["value"], "ar_JO.UTF-8")

    def test_stale_generation_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "generation conflict"):
            registryd._handle({"op": "set", "hive": "environment",
                "path": "environment.locale", "type": "string", "value": "x",
                "generation": 6}, True)

    def test_hardware_identity_keys_are_protected(self):
        with self.assertRaisesRegex(PermissionError, "immutable"):
            registryd._handle({"op": "set", "hive": "machine",
                "path": "cpu.selection.policy", "type": "string", "value": "fake",
                "generation": 1}, True)


    def test_transaction_journal_replays_after_interrupted_commit(self):
        source = json.dumps(self.data, sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as tmp:
            binary = pathlib.Path(tmp) / "prepared.hive"
            subprocess.run(["python3", str(registryd.TOOL), "build", "--input",
                            str(registryd.ROOT / "environment.json"), "--output", str(binary)],
                           check=True, capture_output=True)
            journal = {"hive": "environment",
                       "source": base64.b64encode(source).decode("ascii"),
                       "binary": base64.b64encode(binary.read_bytes()).decode("ascii")}
            (registryd.ROOT / "environment.transaction.json").write_text(json.dumps(journal))
            (registryd.ROOT / "environment.json").write_text("{}")
            registryd._recover("environment")
        restored = json.loads((registryd.ROOT / "environment.json").read_text())
        self.assertEqual(restored["generation"], 7)
        self.assertTrue((registryd.ROOT / "environment.hive").is_file())

    def test_non_admin_cannot_write(self):
        with self.assertRaisesRegex(PermissionError, "group required"):
            registryd._handle({"op": "set", "hive": "environment",
                "path": "environment.locale", "type": "string", "value": "x",
                "generation": 7}, False)

class SmbBrowseTests(unittest.TestCase):
    @mock.patch.object(smb, "run", return_value=(0, "Disk|public|Shared data\nIPC|IPC$|IPC\n", ""))
    def test_explicit_host_uses_kerberos_and_smb2(self, mocked):
        result = smb.browse("files.example.org")
        self.assertEqual(result["shares"][0]["name"], "public")
        argv = mocked.call_args.args[0]
        self.assertIn("--use-kerberos=required", argv)
        self.assertTrue(any("SMB2" in item for item in argv))
        self.assertNotIn("--no-pass", argv)

    def test_host_option_injection_is_rejected(self):
        with self.assertRaises(ValueError):
            smb.browse("-bad-host")

    @mock.patch.object(smb, "ws_discover", return_value=[])
    @mock.patch.object(smb, "run", return_value=(0,
        "=;eth0;IPv4;Office NAS;_smb._tcp;local;nas.local;192.168.1.8;445;\n", ""))
    def test_network_discovery_parses_dns_sd(self, mocked, _wsd_mock):
        result = smb.browse_network()
        self.assertEqual(result["servers"][0]["address"], "192.168.1.8")
        self.assertEqual(mocked.call_args.args[0], ["avahi-browse", "-rt", "_smb._tcp"])


    @mock.patch.object(directory, "run", return_value=SimpleNamespace(returncode=0, stdout="joined", stderr=""))
    def test_ad_join_uses_existing_kerberos_ticket_without_password_prompt(self, mocked):
        old_argv = sys.argv
        try:
            sys.argv = ["directoryctl.py", "join", "example.org", "--user", "admin@example.org"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(directory.main(), 0)
        finally:
            sys.argv = old_argv
        argv = mocked.call_args.args[0]
        self.assertIn("--no-password", argv)
        self.assertIn("--user=admin@example.org", argv)
        self.assertNotIn("--password", argv)

    def test_ad_join_rejects_invalid_domain(self):
        old_argv = sys.argv
        try:
            sys.argv = ["directoryctl.py", "join", "bad..example"]
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(directory.main(), 1)
        finally:
            sys.argv = old_argv

class OpticalImageTests(unittest.TestCase):
    def test_iso9660_primary_volume_descriptor(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "valid.iso"
            data = bytearray(17 * 2048)
            data[16 * 2048] = 1
            data[16 * 2048 + 1:16 * 2048 + 6] = b"CD001"
            path.write_bytes(data)
            self.assertEqual(storage.validate_image(path), path.resolve())

    def test_udf_recognition_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "udf.iso"
            data = bytearray(20 * 2048)
            data[16 * 2048 + 1:16 * 2048 + 6] = b"BEA01"
            data[17 * 2048 + 1:17 * 2048 + 6] = b"NSR03"
            path.write_bytes(data)
            self.assertEqual(storage.validate_image(path), path.resolve())


    @mock.patch.object(storage, "run", side_effect=[
        SimpleNamespace(returncode=0, stdout="udf\n", stderr=""),
        SimpleNamespace(returncode=0, stdout="Mounted /dev/sr0 at /media/user/DVD.\n", stderr="")
    ])
    def test_physical_optical_mount_requests_read_only(self, mocked):
        old_argv = sys.argv
        try:
            sys.argv = ["mount-image.py", "mount-device", "/dev/sr0"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(storage.main(), 0)
        finally:
            sys.argv = old_argv
        self.assertEqual(mocked.call_args_list[1].args[0],
                         ["udisksctl", "mount", "--options", "ro,nodev,nosuid", "--block-device", "/dev/sr0"])

    def test_random_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.iso"
            path.write_bytes(bytes(17 * 2048))
            with self.assertRaisesRegex(ValueError, "volume descriptor"):
                storage.validate_image(path)

if __name__ == "__main__":
    unittest.main()
