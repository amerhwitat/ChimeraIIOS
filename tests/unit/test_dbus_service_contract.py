"""Static D-Bus package safety tests; no live system bus is required."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVICE = ROOT / "services" / "dbus" / "chimera_dbus_service.py"

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

if __name__ == "__main__":
    unittest.main()
