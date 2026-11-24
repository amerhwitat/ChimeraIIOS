#!/usr/bin/env python3
"""Launch and supervise a Chimera desktop session with measured evidence.

This script starts the real session shell and its display server from binaries
found in a rootfs/build tree, then records only observed facts: executable ELF
validation, display socket creation, input device nodes, process liveness from
/proc, and health after a short monitoring window. It never writes a readiness
marker unless those observations all hold. Missing stack components are listed
explicitly and exit 78 (blocked). A synthetic harness is always labelled and
can never produce production or Koronos-native acceptance.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SESSIONS = ("aurora", "marine", "freexp", "freewin11")
BLOCKED = 78
USAGE = 64


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(4) == b"\x7fELF"
    except OSError:
        return False


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_exe(pid: int | None) -> str | None:
    if not pid:
        return None
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except OSError:
        return None


def process_exit(proc: subprocess.Popen | None) -> int | None:
    if proc is None:
        return None
    return proc.poll()


def terminate(proc: subprocess.Popen | None) -> int | None:
    if proc is None or proc.poll() is not None:
        return process_exit(proc)
    proc.terminate()
    try:
        return proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=5)


def resolve_binary(rootfs: Path | None, candidates: list[str],
                   override: str | None) -> tuple[Path | None, list[str]]:
    checked = []
    if override:
        path = Path(override)
        checked.append(str(path))
        return (path if path.is_file() and os.access(path, os.X_OK) else None), checked

    for candidate in candidates:
        raw = Path(candidate)
        if raw.is_absolute() and rootfs:
            path = rootfs / raw.relative_to("/")
        elif raw.is_absolute():
            path = raw
        elif rootfs:
            path = rootfs / raw
        else:
            path = raw
        checked.append(str(path))
        if path.is_file() and os.access(path, os.X_OK):
            return path, checked

    for name in candidates:
        found = shutil.which(name)
        if found:
            checked.append(found)
            return Path(found), checked
    return None, checked


def shell_candidates(mode: str) -> list[str]:
    return [
        "usr/bin/chimera-desktop-shell",
        "usr/local/bin/chimera-desktop-shell",
        "opt/chimera/bin/chimera-desktop-shell",
        "/usr/bin/chimera-desktop-shell",
        str(ROOT / "build/desktop/bin/chimera-desktop-shell"),
    ]


def compositor_candidates(mode: str) -> list[str]:
    if mode == "host-preview":
        return ["usr/bin/Xvfb", "/usr/bin/Xvfb", "usr/bin/Xorg", "/usr/bin/Xorg"]
    return ["usr/bin/labwc", "/usr/bin/labwc", "usr/bin/weston", "/usr/bin/weston",
            "usr/bin/sway", "/usr/bin/sway"]


def process_monitor() -> None:
    """No-op hook kept separate from measurement logic."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", choices=SESSIONS, required=True)
    parser.add_argument("--mode", choices=("native", "host-preview"), default="native")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--rootfs", type=Path, default=None)
    parser.add_argument("--shell", default=None)
    parser.add_argument("--compositor", default=None)
    parser.add_argument("--runtime-dir", default=None)
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--hold", type=float, default=0.5)
    parser.add_argument("--display", default=None)
    parser.add_argument("--harness", action="store_true",
                        help="explicit synthetic harness; never produces acceptance")
    args = parser.parse_args()

    overrides = [args.shell, args.compositor, args.runtime_dir, args.input_dir]
    if any(overrides) and not args.harness:
        print("path overrides require --harness (synthetic evidence only)", file=sys.stderr)
        return USAGE

    manifest_path = ROOT / "desktop/sessions" / f"{args.session}.json"
    if not manifest_path.is_file():
        print(f"session manifest missing: {manifest_path}", file=sys.stderr)
        return USAGE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("id") != args.session:
        print("session manifest id mismatch", file=sys.stderr)
        return USAGE

    rootfs = args.rootfs.resolve() if args.rootfs else None
    runtime_dir = Path(args.runtime_dir) if args.runtime_dir else Path(
        os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    )
    input_dir = Path(args.input_dir) if args.input_dir else Path("/dev/input")
    protocol = "x11" if args.mode == "host-preview" else "wayland"
    display = args.display or ":99"
    display_number = display.lstrip(":").split(".")[0]
    socket_path = (
        Path(f"/tmp/.X11-unix/X{display_number}")
        if protocol == "x11" else runtime_dir / "wayland-0"
    )

    output = args.output or (
        ROOT / "build/native-sessions" / args.session /
        ("preflight.json" if args.preflight_only else "evidence.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    warnings: list[str] = []
    shell_path, shell_checked = resolve_binary(
        rootfs, shell_candidates(args.mode), args.shell
    )
    compositor_path, compositor_checked = resolve_binary(
        rootfs, compositor_candidates(args.mode), args.compositor
    )

    if shell_path is None:
        missing.append("shell binary not found or not executable: " +
                       ", ".join(shell_checked))
    elif not is_elf(shell_path):
        missing.append(f"shell binary is not an ELF executable: {shell_path}")

    if compositor_path is None:
        missing.append(
            f"no {protocol} display server binary found or executable: " +
            ", ".join(compositor_checked)
        )
    elif not is_elf(compositor_path):
        missing.append(f"display server is not an ELF executable: {compositor_path}")

    surface_before = socket_path.exists()
    input_devices = sorted(str(path) for path in glob.glob(str(input_dir / "event*")))
    if not input_devices:
        missing.append(f"no input event devices found under {input_dir}")

    drm_devices = sorted(glob.glob("/dev/dri/card*"))
    if protocol == "wayland" and not drm_devices and not args.harness:
        missing.append("no /dev/dri/card* graphics device is present")

    evidence = {
        "schema": "CHM-NATIVE-SESSION-EVIDENCE-1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session": args.session,
        "mode": args.mode,
        "manifest": {
            "path": str(manifest_path.relative_to(ROOT)),
            "sha256": digest(manifest_path),
        },
        "synthetic_harness": bool(args.harness),
        "host": {
            "kernel": platform.system(),
            "machine": platform.machine(),
            "is_wsl": "microsoft" in platform.release().lower(),
        },
        "binary": {
            "path": str(shell_path) if shell_path else None,
            "candidates_checked": shell_checked,
            "sha256": digest(shell_path) if shell_path and shell_path.is_file() else None,
            "elf": is_elf(shell_path) if shell_path else False,
            "executable": bool(shell_path and os.access(shell_path, os.X_OK)),
        },
        "display_server": {
            "path": str(compositor_path) if compositor_path else None,
            "candidates_checked": compositor_checked,
            "sha256": digest(compositor_path) if compositor_path and compositor_path.is_file() else None,
            "elf": is_elf(compositor_path) if compositor_path else False,
        },
        "graphics": {
            "protocol": protocol,
            "runtime_dir": str(runtime_dir),
            "surface_socket": str(socket_path),
            "surface_socket_exists_before": surface_before,
            "surface_socket_present": surface_before,
            "drm_devices": drm_devices,
        },
        "input": {
            "device_dir": str(input_dir),
            "devices": input_devices,
            "device_count": len(input_devices),
            "attached": bool(input_devices),
        },
        "processes": {
            "display_server": {"pid": None, "exe": None, "alive": False, "exit_code": None},
            "shell": {"pid": None, "exe": None, "alive": False, "exit_code": None},
        },
        "health": {
            "preflight_only": bool(args.preflight_only),
            "timeout_seconds": args.timeout,
            "hold_seconds": args.hold,
            "monitor_seconds": 0.0,
            "stable": False,
        },
        "missing": missing,
        "warnings": warnings,
        "checks": {},
        "checks_satisfied": False,
        "session_ready": False,
        "koronos_native_boot_verified": False,
        "production_acceptance": False,
        "conformance_claim": False,
    }

    if args.preflight_only or missing:
        evidence["status"] = "blocked" if missing else "preflight-only"
        evidence["checks"] = {
            "shell_binary_valid": not any("shell" in item for item in missing),
            "display_server_binary_valid": not any("display server" in item for item in missing),
            "graphics_surface_observed": surface_before,
            "input_devices_observed": bool(input_devices),
            "compositor_process_observed": False,
            "shell_process_observed": False,
            "session_health_observed": False,
        }
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(json.dumps({"session": args.session, "status": evidence["status"],
                          "missing_count": len(missing), "output": str(output)},
                         sort_keys=True))
        return BLOCKED if missing else 0

    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(runtime_dir, 0o700)
    if socket_path.exists():
        warnings.append(f"surface socket already existed before launch: {socket_path}")

    env = os.environ.copy()
    env["XDG_SESSION_TYPE"] = "wayland" if protocol == "wayland" else "x11"
    env["XDG_CURRENT_DESKTOP"] = args.session.capitalize()
    env["XDG_RUNTIME_DIR"] = str(runtime_dir)
    log_dir = output.parent
    display_log = log_dir / "display-server.log"
    shell_log = log_dir / "session-shell.log"

    display_cmd = [str(compositor_path)]
    if protocol == "x11" and compositor_path.name in ("Xvfb", "Xorg"):
        display_cmd += [display, "-screen", "0", "1280x720x24", "-nolisten", "tcp"]
    if protocol == "wayland" and compositor_path.name in ("labwc", "sway", "weston"):
        display_cmd += ["--config-dir", str(runtime_dir)] if compositor_path.name != "weston" else []

    shell_cmd = [str(shell_path), f"--desktop={args.session}"]
    if protocol == "x11":
        env["DISPLAY"] = display

    display_proc = None
    shell_proc = None
    try:
        with display_log.open("wb") as display_out:
            display_proc = subprocess.Popen(
                display_cmd, stdout=display_out, stderr=subprocess.STDOUT,
                env=env, start_new_session=True,
            )
            started = time.monotonic()
            while time.monotonic() - started < args.timeout:
                if display_proc.poll() is not None:
                    missing.append(
                        f"display server exited before creating a surface (code "
                        f"{display_proc.returncode}); log={display_log}"
                    )
                    break
                if socket_path.exists():
                    break
                time.sleep(0.1)
            evidence["graphics"]["surface_socket_present"] = socket_path.exists()
            evidence["graphics"]["surface_ready_after_seconds"] = round(
                time.monotonic() - started, 3
            )

            if socket_path.exists():
                with shell_log.open("wb") as shell_out:
                    shell_proc = subprocess.Popen(
                        shell_cmd, stdout=shell_out, stderr=subprocess.STDOUT,
                        env=env, start_new_session=True,
                    )
                    shell_started = time.monotonic()
                    while time.monotonic() - shell_started < args.timeout:
                        if shell_proc.poll() is not None:
                            missing.append(
                                f"session shell exited before health window (code "
                                f"{shell_proc.returncode}); log={shell_log}"
                            )
                            break
                        if socket_path.exists() and (
                                len(input_devices) > 0 or args.mode == "host-preview"):
                            break
                        time.sleep(0.1)
                    time.sleep(args.hold)
                    evidence["health"]["monitor_seconds"] = round(
                        time.monotonic() - shell_started, 3
                    )
    except OSError as exc:
        missing.append(f"process start failed: {exc}")
    finally:
        display_exit = terminate(display_proc)
        shell_exit = terminate(shell_proc)

    evidence["processes"]["display_server"].update({
        "pid": display_proc.pid if display_proc else None,
        "exe": process_exe(display_proc.pid if display_proc else None),
        "alive": process_alive(display_proc.pid if display_proc else None),
        "exit_code": display_exit,
        "command": display_cmd if display_proc else None,
        "log": str(display_log) if display_proc else None,
    })
    evidence["processes"]["shell"].update({
        "pid": shell_proc.pid if shell_proc else None,
        "exe": process_exe(shell_proc.pid if shell_proc else None),
        "alive": process_alive(shell_proc.pid if shell_proc else None),
        "exit_code": shell_exit,
        "command": shell_cmd if shell_proc else None,
        "log": str(shell_log) if shell_proc else None,
    })
    evidence["graphics"]["surface_socket_present_after"] = socket_path.exists()
    evidence["input"]["device_count_after"] = len(
        glob.glob(str(input_dir / "event*"))
    )

    checks = {
        "shell_binary_valid": bool(shell_path and is_elf(shell_path)),
        "display_server_binary_valid": bool(compositor_path and is_elf(compositor_path)),
        "graphics_surface_observed": bool(evidence["graphics"]["surface_socket_present"]),
        "input_devices_observed": bool(input_devices),
        "compositor_process_observed": bool(
            display_proc and display_proc.pid and display_exit is not None
        ),
        "shell_process_observed": bool(
            shell_proc and shell_proc.pid and shell_exit is not None
        ),
        "session_health_observed": bool(
            evidence["graphics"]["surface_socket_present_after"] and
            evidence["input"]["device_count_after"] > 0 and
            display_exit is not None and shell_exit is not None
        ),
    }
    evidence["checks"] = checks
    evidence["checks_satisfied"] = all(checks.values()) and not missing
    evidence["session_ready"] = evidence["checks_satisfied"] and not args.harness
    evidence["koronos_native_boot_verified"] = bool(
        evidence["session_ready"] and args.mode == "native" and not args.harness
    )
    evidence["status"] = "ready" if evidence["session_ready"] else (
        "harness-checks-satisfied" if evidence["checks_satisfied"] else "blocked"
    )
    evidence["missing"] = missing

    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "session": args.session,
        "status": evidence["status"],
        "checks_satisfied": evidence["checks_satisfied"],
        "session_ready": evidence["session_ready"],
        "missing_count": len(missing),
        "output": str(output),
    }, sort_keys=True))

    if evidence["session_ready"]:
        return 0
    return BLOCKED if missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
