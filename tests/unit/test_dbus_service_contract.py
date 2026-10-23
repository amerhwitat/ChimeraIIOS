"""Static D-Bus package safety tests; no live system bus is required."""
import ast
import pathlib
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
DBUS = ROOT / "services" / "dbus"
SERVICE = DBUS / "chimera_dbus_service.py"

class DbusServiceContractTests(unittest.TestCase):
    def test_python_parses(self):
        ast.parse(SERVICE.read_text(encoding="utf-8"))

    def test_read_only_allowlisted_api(self):
        source = SERVICE.read_text(encoding="utf-8")
        for name in ("Ping", "GetStatus", "ListServices"):
            self.assertIn("def " + name + "(", source)
        for forbidden in ("def Execute(", "def RunCommand(", "def SetUser(", "def PowerOff("):
            self.assertNotIn(forbidden, source)
        self.assertIn("subprocess.run(argv", source)
        self.assertNotIn("shell=True", source)

    def test_daemon_stays_alive(self):
        source = SERVICE.read_text(encoding="utf-8")
        self.assertIn("await asyncio.get_running_loop().create_future()", source)
        self.assertIn("await bus.request_name(BUS_NAME)", source)

    def test_bus_policy_is_valid_and_read_only(self):
        policy = next(DBUS.glob("org.*.OS.conf"))
        root = ET.parse(policy).getroot()
        self.assertEqual(root.tag, "busconfig")
        allowed = {node.attrib.get("send_member") for node in root.findall(".//allow")
                   if node.attrib.get("send_member")}
        self.assertEqual(allowed, {"Ping", "GetStatus", "ListServices"})
        self.assertTrue(any("own" in node.attrib for node in root.findall(".//allow")))

    def test_unit_and_activation_agree(self):
        unit = next(DBUS.glob("*-dbus.service"))
        activation = next(DBUS.glob("org.*.OS.service"))
        unit_text = unit.read_text(encoding="utf-8")
        activation_text = activation.read_text(encoding="utf-8")
        name = next(line.split("=", 1)[1] for line in activation_text.splitlines()
                    if line.startswith("Name="))
        self.assertIn("Type=dbus", unit_text)
        self.assertIn("BusName=" + name, unit_text)
        self.assertIn("Restart=on-failure", unit_text)
        self.assertIn("NoNewPrivileges=true", unit_text)
        self.assertIn("SystemdService=" + unit.name, activation_text)

    def test_sysv_actions_are_present(self):
        wrapper = next(DBUS.glob("*.init")).read_text(encoding="utf-8")
        for action in ("start", "stop", "restart", "status"):
            self.assertIn(action, wrapper)

if __name__ == "__main__":
    unittest.main()
