#!/usr/bin/env python3
"""Install available, genuine Debian terminal and shell packages; never fabricate launchers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

TERMINAL_PACKAGES = {
    "alacritty": ("alacritty", "Alacritty", "طرفية Alacritty"),
    "blackbox-terminal": ("blackbox", "Black Box Terminal", "طرفية Black Box"),
    "contour": ("contour", "Contour", "طرفية Contour"),
    "foot": ("foot", "Foot Terminal", "طرفية Foot"),
    "ghostty": ("ghostty", "Ghostty", "طرفية Ghostty"),
    "gnome-console": ("kgx", "GNOME Console", "طرفية GNOME Console"),
    "gnome-terminal": ("gnome-terminal", "GNOME Terminal", "طرفية GNOME"),
    "kitty": ("kitty", "Kitty", "طرفية Kitty"),
    "konsole": ("konsole", "Konsole", "طرفية Konsole"),
    "lxterminal": ("lxterminal", "LXTerminal", "طرفية LX"),
    "mate-terminal": ("mate-terminal", "MATE Terminal", "طرفية MATE"),
    "ptyxis": ("ptyxis", "Ptyxis", "طرفية Ptyxis"),
    "qterminal": ("qterminal", "QTerminal", "طرفية QTerminal"),
    "sakura": ("sakura", "Sakura", "طرفية Sakura"),
    "terminator": ("terminator", "Terminator", "طرفية Terminator"),
    "terminology": ("terminology", "Terminology", "طرفية Terminology"),
    "tilix": ("tilix", "Tilix", "طرفية Tilix"),
    "wezterm": ("wezterm", "WezTerm", "طرفية WezTerm"),
    "xfce4-terminal": ("xfce4-terminal", "XFCE Terminal", "طرفية XFCE"),
    "xterm": ("xterm", "XTerm", "طرفية XTerm"),
}
SHELL_PACKAGES = {
    "bash": ("bash", "bash"),
    "zsh": ("zsh", "zsh"),
    "fish": ("fish", "fish"),
    "dash": ("dash", "dash"),
    "mksh": ("mksh", "mksh"),
    "yash": ("yash", "yash"),
    "elvish": ("elvish", "elvish"),
    "nushell": ("nushell", "nu"),
}

def run(args: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=False)

def candidate(package: str) -> bool:
    result = run(["apt-cache", "policy", package], timeout=60)
    for line in result.stdout.splitlines():
        if line.strip().startswith("Candidate:"):
            value = line.split(":", 1)[1].strip()
            return bool(value and value != "(none)")
    return False

def install(package: str) -> tuple[bool, str]:
    if not candidate(package):
        return False, "package-unavailable-in-configured-repositories"
    result = run(["apt-get", "install", "-y", "--no-install-recommends", package])
    if result.returncode:
        return False, "package-install-failed: " + result.stderr[-1200:]
    return True, "package-installed"

def executable(binary: str) -> str | None:
    path = shutil.which(binary)
    return path if path and os.access(path, os.X_OK) else None

def digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--terminal-registry", type=Path, required=True)
    ap.add_argument("--shell-registry", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("/usr/share/chimera/catalogs/terminal-shell-installation.json"))
    args = ap.parse_args()
    terminal_registry = json.loads(args.terminal_registry.read_text(encoding="utf-8"))
    shell_registry = json.loads(args.shell_registry.read_text(encoding="utf-8"))
    rows = {"terminals": [], "shells": []}
    for item in terminal_registry.get("entries", []):
        ident = item.get("id", "")
        binary, display, arabic = TERMINAL_PACKAGES.get(ident, (item.get("binary", ""), item.get("name", ident), item.get("name", ident)))
        ok, status = install(ident)
        path = executable(binary)
        if not path and ok:
            status = "package-installed-but-expected-executable-missing"
        row = {"id": ident, "package": ident, "binary": binary, "status": status,
               "path": path, "source": item.get("source"), "license": item.get("license")}
        if path:
            row["sha256"] = digest(path)
            desktop_dir = Path("/usr/share/applications")
            desktop_dir.mkdir(parents=True, exist_ok=True)
            (desktop_dir / f"chimera-terminal-{ident}.desktop").write_text(
                "[Desktop Entry]\nType=Application\nVersion=1.0\n"
                f"Name=Chimera: {display}\nName[ar]={arabic}\n"
                "Comment=Aurora verified terminal provider\n"
                f"Exec={binary}\nIcon=utilities-terminal\nTerminal=false\n"
                "Categories=System;TerminalEmulator;Utility;Development;\n"
                "StartupNotify=true\n", encoding="utf-8")
            row["desktop_entry"] = f"/usr/share/applications/chimera-terminal-{ident}.desktop"
        rows["terminals"].append(row)
    for item in shell_registry.get("entries", []):
        ident = item.get("id", "")
        package, binary = SHELL_PACKAGES.get(ident, (ident, item.get("binary", ident)))
        ok, status = install(package)
        path = executable(binary)
        if not path and ok:
            status = "package-installed-but-expected-executable-missing"
        row = {"id": ident, "package": package, "binary": binary, "status": status,
               "path": path, "source": item.get("source"), "license": item.get("license")}
        if path:
            row["sha256"] = digest(path)
            probe = run([path, "-c", "printf 'CHIMERA_SHELL_OK\\n'"], timeout=20)
            row["runtime_status"] = "shell-command-smoke-tested" if probe.returncode == 0 and "CHIMERA_SHELL_OK" in probe.stdout else "executable-present-smoke-test-failed"
            if row["runtime_status"] == "executable-present-smoke-test-failed":
                row["smoke_stderr"] = probe.stderr[-500:]
        rows["shells"].append(row)
    result = {
        "schema": "CHIMERA-OPEN-SOURCE-TERMINALS-SHELLS-1",
        "policy": "Only package-managed executable providers are listed as present. Package absence or installation failures remain explicit; no placeholder binaries are created. Shell smoke tests are Linux userspace tests, not Koronos ABI tests.",
        "terminals": rows["terminals"], "shells": rows["shells"],
        "summary": {
            "terminals_registered": len(rows["terminals"]),
            "terminals_present": sum(bool(x["path"]) for x in rows["terminals"]),
            "shells_registered": len(rows["shells"]),
            "shells_present": sum(bool(x["path"]) for x in rows["shells"]),
            "shells_smoke_tested": sum(x.get("runtime_status") == "shell-command-smoke-tested" for x in rows["shells"]),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
