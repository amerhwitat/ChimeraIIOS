"""End-to-end D-Bus wire test using an isolated session bus."""
import asyncio
import json
import os
import pathlib
import sys
import unittest
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType

ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVICE = ROOT / "services" / "dbus" / "chimera_dbus_service.py"
BUS_NAME = "org.chimera.Test"
OBJECT_PATH = "/org/chimera/Test"
INTERFACE = "org.chimera.Test"

class DbusWireIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        env = os.environ.copy()
        env.update({
            "CHIMERA_DBUS_BUS_TYPE": "session",
            "CHIMERA_DBUS_NAME": BUS_NAME,
            "CHIMERA_DBUS_PATH": OBJECT_PATH,
            "CHIMERA_DBUS_INTERFACE": INTERFACE,
            "CHIMERA_OS_NAME": "D-Bus-Test",
        })
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, str(SERVICE),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
        )
        self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
        self.proxy = None
        for _ in range(100):
            if self.process.returncode is not None:
                _, stderr = await self.process.communicate()
                self.fail("service exited early: " + stderr.decode(errors="replace"))
            try:
                intro = await self.bus.introspect(BUS_NAME, OBJECT_PATH)
                obj = self.bus.get_proxy_object(BUS_NAME, OBJECT_PATH, intro)
                self.proxy = obj.get_interface(INTERFACE)
                break
            except Exception:
                await asyncio.sleep(0.05)
        if self.proxy is None:
            self.fail("D-Bus service did not acquire its name/export its interface")

    async def asyncTearDown(self):
        if self.bus:
            self.bus.disconnect()
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

    async def test_ping_get_status_and_list_services(self):
        self.assertEqual(await self.proxy.call_ping(), "pong")
        status = json.loads(await self.proxy.call_get_status())
        self.assertEqual(status["service"], "koronos-dbus-status")
        self.assertEqual(status["os"], "D-Bus-Test")
        self.assertEqual(status["bus_name"], BUS_NAME)
        services = json.loads(await self.proxy.call_list_services())
        self.assertIsInstance(services, dict)
        self.assertIn("ok", services)

if __name__ == "__main__":
    unittest.main()
