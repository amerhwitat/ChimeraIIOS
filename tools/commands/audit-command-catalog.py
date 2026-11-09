#!/usr/bin/env python3
"""Generate a non-executing per-command provider inventory from the canonical catalog."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

NAMESPACES = {
    "linux_bash": "linux-bash",
    "macos_core": "macos",
    "windows_cmd_core": "windows-cmd",
    "powershell_core": "powershell",
    "vbscript_core": "vbscript",
    "sql_server_core": "sql-server",
    "native_chimera": "native-chimera",
}
SEARCH_DIRS = ("usr/bin", "bin", "usr/sbin", "sbin", "usr/local/bin", "usr/local/sbin")


def command_name(item: object) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        for key in ("name", "command", "id"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def bash_words(shell: str, option: str) -> set[str]:
    if not shutil.which(shell):
        return set()
    try:
        proc = subprocess.run([shell, "-c", option], check=False, capture_output=True, text=True, timeout=5)
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    except (OSError, subprocess.SubprocessError):
        return set()


def resolve(root: Path, name: str) -> Path | None:
    if not name or "/" in name:
        return None
    for directory in SEARCH_DIRS:
        candidate = root / directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def elf_machine(path: Path) -> str | None:
    readelf = shutil.which("readelf")
    if not readelf:
        return None
    try:
        proc = subprocess.run([readelf, "-h", str(path)], check=False, capture_output=True, text=True, timeout=5)
        for line in proc.stdout.splitlines():
            if "Machine:" in line:
                return line.split("Machine:", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("system/commands/chimera-command-list.json"))
    parser.add_argument("--rootfs", type=Path, default=Path("/"))
    parser.add_argument("--output", type=Path, default=Path("command-catalog-provider-ledger.json"))
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    root = args.rootfs.resolve()
    builtins = bash_words("bash", "compgen -b")
    reserved = bash_words("bash", "compgen -k")
    rows = []
    providers = {}
    for key in ("bash", "pwsh", "wine", "cscript.exe", "wscript.exe", "sqlcmd", "bash"):
        found = shutil.which(key)
        providers[key] = found
    seen = set()
    for namespace, platform in NAMESPACES.items():
        for raw in catalog.get(namespace, []):
            name = command_name(raw)
            if not name:
                continue
            identity = (namespace, name)
            if identity in seen:
                continue
            seen.add(identity)
            binary = resolve(root, name)
            status = "provider-present" if binary else "provider-not-found"
            if namespace == "linux_bash" and not binary:
                if name in builtins:
                    status = "bash-builtin"
                elif name in reserved:
                    status = "bash-reserved-word"
            elif namespace == "native_chimera" and not binary:
                status = "native-provider-missing"
            elif namespace == "macos_core" and not binary:
                status = "darwin-runtime-required"
            elif namespace == "windows_cmd_core" and not binary:
                status = "windows-cmd-runtime-required"
            elif namespace == "powershell_core" and not binary:
                status = "powershell-runtime-required"
            elif namespace == "vbscript_core" and not binary:
                status = "vbscript-runtime-required"
            elif namespace == "sql_server_core" and not binary:
                status = "sql-runtime-required"
            row = {"namespace": namespace, "platform": platform, "command": name, "status": status}
            if binary:
                resolved = binary.resolve()
                row.update({
                    "path": "/" + str(binary.relative_to(root)).replace(os.sep, "/"),
                    "sha256": sha256(resolved),
                    "elf_machine": elf_machine(resolved),
                })
            rows.append(row)
    counts = {}
    for row in rows:
        key = row["status"]
        counts[key] = counts.get(key, 0) + 1
    output = {
        "schema": "CHM-COMMAND-CATALOG-PROVIDER-LEDGER-1",
        "catalog": str(args.catalog),
        "rootfs": str(root),
        "execution_performed": False,
        "providers": providers,
        "namespace_entry_count": len(rows),
        "unique_command_names": len({row["command"] for row in rows}),
        "status_counts": counts,
        "commands": rows,
        "note": "Provider presence and hashes do not prove command semantics, option compatibility, security, or conformance.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"[Chimera][COMMAND-CATALOG] entries={len(rows)} unique={output['unique_command_names']} statuses={json.dumps(counts, sort_keys=True)}")
    print(f"[Chimera][COMMAND-CATALOG] ledger={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
