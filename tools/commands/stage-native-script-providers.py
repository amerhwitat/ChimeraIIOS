#!/usr/bin/env python3
"""Stage real Chimera userland tools into a Linux target rootfs.

The installed launchers dispatch to repository source bundled under
/opt/aurora/repo. C/C++ utilities are compiled from their real sources. Missing
source files or failed builds are reported as missing; no placeholder is emitted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

# command -> (repository source, interpreter)
SCRIPTS = {
    "chimera-help": ("tools/help/chimera-help", "python"),
    "chimera-info": ("tools/commands/chimera-info.py", "python"),
    "chimera-doctor": ("tools/commands/chimera-doctor.py", "python"),
    "chimera-update": ("tools/commands/chimera-update.sh", "bash"),
    "chimera-package": ("package-manager/chimera-pkg.py", "python"),
    "korectl": ("tools/runtime/chimera-korectl.py", "python"),
    "chimera-service": ("tools/runtime/chimera-service.py", "python"),
    "chimera-display": ("tools/display/chimera-display", "bash"),
    "chimera-python": ("sdk/bin/chimera-python", "sh"),
    "chimera-java": ("sdk/bin/chimera-java", "sh"),
    "chimera-background": ("tools/branding/chimera-background", "bash"),
    "chimera-gpu-driver-manager": ("tools/display/chimera-gpu-driver-manager", "bash"),
    "chimera-hardware-drivers": ("tools/drivers/chimera-hardware-drivers", "bash"),
    "chimera-driver-panel": ("tools/drivers/chimera-driver-panel.py", "python"),
    "chimera-shell": ("system/shell/chimera-shell.sh", "bash"),
    "chimera-terminal": ("tools/terminal/chimera-terminal", "python"),
    "chimera": ("tools/runtime/chimera-command.py", "python"),
    "chimera-cmd": ("tools/commands/chimera-cmd", "bash"),
    "chimera-run": ("tools/commands/chimera-run", "python"),
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--rootfs", type=Path, required=True)
    ap.add_argument("--build-dir", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    rootfs = args.rootfs.resolve()
    build = args.build_dir.resolve()
    bindir = rootfs / "usr/bin"
    bindir.mkdir(parents=True, exist_ok=True)
    rows = []

    for command, (relative, interpreter) in SCRIPTS.items():
        source = repo / relative
        if not source.is_file():
            rows.append({"command": command, "source": relative, "status": "source-missing"})
            continue
        if interpreter == "python":
            prefix = "#!/bin/sh\nexec /usr/bin/python3 /opt/aurora/repo/" + relative + ' "$@"\n'
        elif interpreter == "bash":
            prefix = "#!/bin/sh\nexec /bin/bash /opt/aurora/repo/" + relative + ' "$@"\n'
        else:
            prefix = "#!/bin/sh\nexec /bin/sh /opt/aurora/repo/" + relative + ' "$@"\n'
        target = bindir / command
        target.write_text(prefix, encoding="utf-8")
        target.chmod(0o755)
        rows.append({"command": command, "source": relative, "path": "/usr/bin/" + command,
                     "status": "source-backed-launcher-staged", "sha256": sha(source)})

    # Reuse the real chmctl binary already built by build-chimera-native-tools.sh.
    # Build it here only when the earlier native-tool stage did not provide it.
    compiler = shutil.which("g++")
    chmctl_source = repo / "userland/commands/chmctl.cpp"
    chmctl = bindir / "chmctl"
    chimeractl = bindir / "chimeractl"
    if not (chmctl.is_file() and chmctl.stat().st_mode & 0o111):
        if compiler and chmctl_source.is_file():
            proc = subprocess.run([compiler, "-std=c++17", "-O2", "-Wall", "-Wextra",
                                   str(chmctl_source), "-o", str(chmctl)],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode:
                chmctl.unlink(missing_ok=True)
                rows.append({"command": "chmctl", "source": "userland/commands/chmctl.cpp",
                             "status": "compile-failed", "stderr": proc.stderr[-3000:]})
            else:
                chmctl.chmod(0o755)
                rows.append({"command": "chmctl", "source": "userland/commands/chmctl.cpp",
                             "path": "/usr/bin/chmctl", "status": "compiled-from-source",
                             "sha256": sha(chmctl)})
        else:
            rows.append({"command": "chmctl", "source": "userland/commands/chmctl.cpp",
                         "status": "compiler-or-source-missing"})
    else:
        rows.append({"command": "chmctl", "source": "userland/commands/chmctl.cpp",
                     "path": "/usr/bin/chmctl", "status": "verified-existing-compiled-provider",
                     "sha256": sha(chmctl)})
    if chmctl.is_file() and chmctl.stat().st_mode & 0o111:
        if not chimeractl.exists() and not chimeractl.is_symlink():
            chimeractl.symlink_to("chmctl")
        elif chimeractl.is_symlink() and chimeractl.resolve() != chmctl.resolve():
            chimeractl.unlink()
            chimeractl.symlink_to("chmctl")
        if chimeractl.is_file() and chimeractl.stat().st_mode & 0o111:
            rows.append({"command": "chimeractl", "path": "/usr/bin/chimeractl",
                         "status": "verified-alias-to-chmctl"})

    # build-chimera-native-tools.sh normally compiled and installed these tools.
    # Reuse those binaries; only invoke CMake as a fallback when an output is absent.
    binaries = {"chimera-asm": bindir / "chimera-asm",
                "chimera-disasm": bindir / "chimera-disasm",
                "chimera-re": bindir / "chimera-re"}
    missing_binaries = [name for name, path in binaries.items()
                        if not (path.is_file() and path.stat().st_mode & 0o111)]
    if missing_binaries:
        asm_source = repo / "tools/chimera-asm"
        cmake = shutil.which("cmake")
        if cmake and (asm_source / "CMakeLists.txt").is_file():
            asm_build = build / "chimera-asm"
            proc = subprocess.run([cmake, "-S", str(asm_source), "-B", str(asm_build),
                                   "-DCMAKE_BUILD_TYPE=Release"],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0:
                proc = subprocess.run([cmake, "--build", str(asm_build), "--parallel", "2"],
                                      text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0:
                outputs = {"chimera-asm": asm_build / "chimera-as",
                           "chimera-disasm": asm_build / "chimera-dis",
                           "chimera-re": asm_build / "chimera-re"}
                for name in missing_binaries:
                    source = outputs[name]
                    if source.is_file():
                        shutil.copy2(source, binaries[name])
                        binaries[name].chmod(0o755)
                    else:
                        rows.append({"command": name, "status": "build-output-missing"})
            else:
                rows.append({"command": "chimera-asm-suite", "status": "compile-failed",
                             "stderr": proc.stderr[-3000:]})
        else:
            rows.append({"command": "chimera-asm-suite", "status": "cmake-or-source-missing"})
    for name, path in binaries.items():
        if path.is_file() and path.stat().st_mode & 0o111:
            rows.append({"command": name, "path": "/usr/bin/" + name,
                         "status": "verified-compiled-assembler-provider", "sha256": sha(path)})

    # Include the runtime manifests at the paths expected by the actual tools.
    for relative, destination in (
        ("system/commands/chimera-command-list.json", "usr/share/chimera/commands/chimera-command-list.json"),
        ("system/commands/chimera-arabic.json", "usr/share/chimera/commands/chimera-arabic.json"),
        ("system/commands/ss64-command-catalog.json", "usr/share/chimera/commands/ss64-command-catalog.json"),
        ("tools/commands/os-command-runtime.json", "usr/share/chimera/commands/os-command-runtime.json"),
    ):
        source = repo / relative
        if source.is_file():
            dest = rootfs / destination
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)

    report = {
        "schema": "CHIMERA-NATIVE-SCRIPT-PROVIDERS-1",
        "policy": "Each launcher points to a real repository implementation bundled in /opt/aurora/repo; compiled tools are built from source. Presence is not proof of Koronos syscall compatibility or service-backend availability.",
        "provider_count": len(rows),
        "counts": {},
        "providers": rows,
    }
    for row in rows:
        report["counts"][row["status"]] = report["counts"].get(row["status"], 0) + 1
    out = rootfs / "usr/share/chimera/commands/native-script-provider-staging.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"provider_count": len(rows), "counts": report["counts"]}, sort_keys=True))
    failures = [r for r in rows if r["status"] in ("source-missing", "compile-failed",
                "compiler-or-source-missing", "cmake-or-source-missing", "build-output-missing")]
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
