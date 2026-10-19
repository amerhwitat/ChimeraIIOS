#!/usr/bin/env python3
"""Read-only D-Bus status API for the Chimera/Octavian hosted runtime.

This is a D-Bus service, not a bus broker. It requires a running system bus
and dbus-next. It intentionally exposes no shell or privileged mutation API.
"""
from __future__ import annotations
import asyncio, json, os, platform, shutil, subprocess
from typing import Any
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next.service import ServiceInterface, method

BUS_NAME = os.environ.get("CHIMERA_DBUS_NAME", "org.chimera.OS")
OBJECT_PATH = os.environ.get("CHIMERA_DBUS_PATH", "/org/chimera/OS")
INTERFACE = os.environ.get("CHIMERA_DBUS_INTERFACE", BUS_NAME)

def _run(argv: list[str], timeout: float = 2.0) -> dict[str, Any]:
    """Run a fixed allow-listed diagnostic command without a shell."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {"ok": result.returncode == 0, "code": result.returncode,
                "stdout": result.stdout[-8192:], "stderr": result.stderr[-4096:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}

class OperatingSystemStatus(ServiceInterface):
    """Small, read-only status interface for the system bus."""
    def __init__(self) -> None:
        super().__init__(INTERFACE)

    @method()
    def Ping(self) -> "s":
        return "pong"

    @method()
    def GetStatus(self) -> "s":
        data = {"service": "koronos-dbus-status",
                "os": os.environ.get("CHIMERA_OS_NAME", "ChimeraIIOS"),
                "pid": os.getpid(), "uid": os.getuid(), "euid": os.geteuid(),
                "hostname": platform.node(), "kernel": platform.release(),
                "systemd_available": shutil.which("systemctl") is not None,
                "bus_name": BUS_NAME}
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @method()
    def ListServices(self) -> "s":
        if not shutil.which("systemctl"):
            return json.dumps({"ok": False, "error": "systemctl unavailable"})
        return json.dumps(_run(["systemctl", "list-units", "--type=service", "--all",
                                "--no-pager", "--plain"]),
                          sort_keys=True, separators=(",", ":"))

async def serve() -> None:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    bus.export(OBJECT_PATH, OperatingSystemStatus())
    await bus.request_name(BUS_NAME)
    # Stay alive for service-manager supervision; do not return after readiness.
    await asyncio.get_running_loop().create_future()

def main() -> None:
    asyncio.run(serve())

if __name__ == "__main__":
    main()
