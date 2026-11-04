import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
smb = load("smb_browse", "services/network/smb-browse.py")
directory = load("directoryctl", "services/network/directoryctl.py")
media = load("mount_image", "services/storage/mount-image.py")

class NetworkAndStorageTests(unittest.TestCase):
    def test_smb_host_is_explicit_and_validated(self):
        with self.assertRaises(ValueError):
            smb.browse("server/share")
        with self.assertRaises(ValueError):
            smb.browse("server;touch")

    def test_smb_requires_kerberos_and_uses_smb2(self):
        with patch.object(smb, "run", return_value=(0, "DISK|data|Files", "")) as run:
            result = smb.browse("files.example.org")
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["shares"][0]["name"], "data")
        self.assertIn("--option=client min protocol=SMB2", run.call_args.args[0])
        with self.assertRaises(ValueError):
            smb.browse("files.example.org", kerberos=False)

    def test_local_discovery_merges_ws_discovery_and_mdns(self):
        avahi = "=;eth0;IPv4;files;_smb._tcp;local;files.local;192.0.2.10;445;\n"
        with patch.object(smb, "run", return_value=(0, avahi, "")), \
             patch.object(smb, "ws_discover", return_value=[{"address": "192.0.2.11", "discovery": "WS-Discovery"}]):
            result = smb.browse_network()
        self.assertEqual(len(result["servers"]), 2)
        self.assertIn("WS-Discovery Probe", result["discovery"])

    def test_directory_domain_and_ldap_uri_validation(self):
        self.assertTrue(directory.DOMAIN.fullmatch("corp.example.org"))
        self.assertFalse(directory.DOMAIN.fullmatch("corp;example"))
        self.assertTrue(directory.URI.fullmatch("ldaps://dc.example.org:636"))
        self.assertFalse(directory.URI.fullmatch("ldap://dc.example.org/path"))

    def make_image(self, udf=False):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        path = pathlib.Path(tmp.name)
        data = bytearray(40 * 2048)
        if udf:
            data[16 * 2048 + 1:16 * 2048 + 6] = b"BEA01"
            data[17 * 2048 + 1:17 * 2048 + 6] = b"NSR02"
        else:
            data[16 * 2048] = 1
            data[16 * 2048 + 1:16 * 2048 + 6] = b"CD001"
        path.write_bytes(data)
        return path

    def test_iso9660_and_udf_images_are_recognized(self):
        for udf in (False, True):
            path = self.make_image(udf)
            try:
                self.assertEqual(media.validate_image(path), path.resolve())
            finally:
                path.unlink()

    def test_invalid_optical_image_rejected(self):
        with tempfile.NamedTemporaryFile() as image:
            image.write(b"not an ISO")
            image.flush()
            with self.assertRaises(ValueError):
                media.validate_image(image.name)

if __name__ == "__main__":
    unittest.main()
