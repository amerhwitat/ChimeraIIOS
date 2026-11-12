#!/usr/bin/env python3
"""Generate evidence-preserving command and ISA cross-platform crosswalks.

The command catalogue stores names, not option grammars or executable status.
This generator therefore records exact namespace matches and curated semantic
aliases separately, and never upgrades a catalogue row to "implemented".
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = ROOT / "system/commands/chimera-command-list.json"
ISA = ROOT / "isa/isa_database.json"
BACKENDS = ROOT / "tools/isa/architecture-backends.json"
OUT = ROOT / "system/commands/generated-cross-platform-crosswalk.json"

# Curated semantic equivalents. These are operation-level hints, not claims
# that flags, quoting, streams, permissions, or exit semantics are identical.
ALIASES = {
    "ls": {"windows_cmd": ["dir"], "powershell": ["Get-ChildItem"]},
    "dir": {"linux_bash": ["ls"], "macos": ["ls"], "powershell": ["Get-ChildItem"]},
    "cd": {"windows_cmd": ["cd", "chdir"], "powershell": ["Set-Location"]},
    "pwd": {"windows_cmd": ["cd"], "powershell": ["Get-Location"]},
    "cp": {"windows_cmd": ["copy", "xcopy"], "powershell": ["Copy-Item"]},
    "copy": {"linux_bash": ["cp"], "macos": ["cp"], "powershell": ["Copy-Item"]},
    "mv": {"windows_cmd": ["move"], "powershell": ["Move-Item"]},
    "move": {"linux_bash": ["mv"], "macos": ["mv"], "powershell": ["Move-Item"]},
    "rm": {"windows_cmd": ["del", "erase"], "powershell": ["Remove-Item"]},
    "del": {"linux_bash": ["rm"], "macos": ["rm"], "powershell": ["Remove-Item"]},
    "cat": {"windows_cmd": ["type"], "powershell": ["Get-Content"]},
    "type": {"linux_bash": ["cat"], "macos": ["cat"], "powershell": ["Get-Content"]},
    "grep": {"windows_cmd": ["findstr"], "powershell": ["Select-String"]},
    "findstr": {"linux_bash": ["grep"], "macos": ["grep"], "powershell": ["Select-String"]},
    "find": {"powershell": ["Get-ChildItem -Recurse"]},
    "mkdir": {"windows_cmd": ["md"], "powershell": ["New-Item -ItemType Directory"]},
    "md": {"linux_bash": ["mkdir"], "macos": ["mkdir"], "powershell": ["New-Item -ItemType Directory"]},
    "ps": {"windows_cmd": ["tasklist"], "powershell": ["Get-Process"]},
    "tasklist": {"linux_bash": ["ps"], "macos": ["ps"], "powershell": ["Get-Process"]},
    "kill": {"windows_cmd": ["taskkill"], "powershell": ["Stop-Process"]},
    "taskkill": {"linux_bash": ["kill"], "macos": ["kill"], "powershell": ["Stop-Process"]},
    "ip": {"windows_cmd": ["ipconfig"], "powershell": ["Get-NetIPConfiguration"]},
    "ipconfig": {"linux_bash": ["ip"], "macos": ["ifconfig"], "powershell": ["Get-NetIPConfiguration"]},
    "ss": {"windows_cmd": ["netstat"], "powershell": ["Get-NetTCPConnection"]},
    "netstat": {"linux_bash": ["ss"], "macos": ["netstat"], "powershell": ["Get-NetTCPConnection"]},
    "curl": {"powershell": ["Invoke-WebRequest", "Invoke-RestMethod"]},
    "chmod": {"windows_cmd": ["icacls"], "powershell": ["Set-Acl"]},
    "icacls": {"linux_bash": ["chmod", "chown"], "macos": ["chmod", "chown"]},
    "df": {"windows_cmd": ["fsutil volume diskfree"], "powershell": ["Get-Volume"]},
    "mount": {"windows_cmd": ["mountvol"], "powershell": ["Get-Volume", "Mount-DiskImage"]},
    "systemctl": {"windows_cmd": ["sc.exe"], "powershell": ["Get-Service", "Start-Service", "Stop-Service"]},
    "sc.exe": {"linux_bash": ["systemctl"], "macos": ["launchctl"], "powershell": ["Get-Service"]},
    "man": {"windows_cmd": ["help", "/?"], "powershell": ["Get-Help"]},
    "launchctl": {"linux_bash": ["systemctl"], "windows_cmd": ["sc.exe"]},
    "open": {"linux_bash": ["xdg-open"], "windows_cmd": ["start"], "powershell": ["Start-Process"]},
    "xdg-open": {"macos": ["open"], "windows_cmd": ["start"], "powershell": ["Start-Process"]},
}

NAMESPACE_KEYS = {
    "linux_bash": "linux_bash",
    "macos": "macos_core",
    "windows_cmd": "windows_cmd_core",
    "powershell": "powershell_core",
    "vbscript": "vbscript_core",
    "sql_server": "sql_server_core",
    "native_chimera": "native_chimera",
}

ARCH_ALIASES = {
    "x86-64": "x86_64", "x86-32": "x86", "i386": "x86",
    "arm32": "armv7", "arm32-thumb": "armv7", "aarch64": "aarch64",
    "mips32": "mips", "powerpc": "powerpc", "s390x": "s390x",
    "riscv64": "riscv64", "riscv32": "riscv32", "z80": "dos-x86",
    "6502": "dos-x86", "m68k": "unknown", "avr": "unknown",
    "8051": "unknown", "chimera-c8192": "unknown", "chimera-r8192": "unknown",
}

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def command_crosswalk():
    doc = read_json(COMMANDS)
    by_name = defaultdict(set)
    for namespace, key in NAMESPACE_KEYS.items():
        for item in doc.get(key, []):
            if isinstance(item, str):
                by_name[item].add(namespace)
    rows = []
    for name in sorted(by_name, key=lambda x: (x.lower(), x)):
        exact = sorted(by_name[name])
        semantic = ALIASES.get(name.lower(), {})
        equivalents = {}
        for platform in ("linux_bash", "macos", "windows_cmd", "powershell"):
            values = []
            if platform in exact:
                values.append({"name": name, "match": "exact-catalogue-name"})
            for alias in semantic.get(platform, []):
                values.append({"name": alias, "match": "curated-semantic-equivalent"})
            if values:
                equivalents[platform] = values
        rows.append({
            "id": norm(name),
            "name": name,
            "catalogue_namespaces": exact,
            "platform_equivalents": equivalents,
            "options_coverage": "not-present-in-source-catalogue",
            "provider_status": "not-asserted-by-name-catalogue",
            "native_implementation": "must-be-established-by-provider-ledger-and-tests",
        })
    return {
        "schema": "CHM-CROSS-PLATFORM-COMMAND-CROSSWALK-1",
        "source": str(COMMANDS.relative_to(ROOT)),
        "namespace_counts": {ns: len(doc.get(key, [])) for ns, key in NAMESPACE_KEYS.items()},
        "unique_command_names": len(rows),
        "policy": "Exact name matches and curated semantic equivalents are separate; no option or binary support is inferred.",
        "commands": rows,
    }

def isa_crosswalk():
    db, backends = read_json(ISA), read_json(BACKENDS)
    instructions = defaultdict(list)
    for row in db.get("instructions", []):
        if len(row) >= 5:
            instructions[row[0]].append({
                "mnemonic": row[1], "form_id": row[2],
                "operands": row[3], "syntax": row[4],
                "length_bits": row[5] if len(row) > 5 else None,
            })
    targets = backends.get("architectures", {})
    rows = []
    for row in db.get("architectures", []):
        if len(row) < 8:
            continue
        arch_id, klass, family, bits, status, encoding, source_ref, form_count = row[:8]
        backend_id = ARCH_ALIASES.get(arch_id, norm(arch_id).replace("-", "_"))
        backend = targets.get(backend_id, {})
        rows.append({
            "architecture_id": arch_id,
            "class": klass,
            "family": family,
            "word_bits": bits,
            "catalogue_status": status,
            "encoding_model": encoding,
            "source_ref": source_ref,
            "instruction_rows": instructions.get(arch_id, []),
            "backend_match": backend_id if backend else None,
            "llvm_targets": backend.get("llvm_targets", []),
            "qemu_user": backend.get("qemu_user"),
            "foreign_runtime": backend.get("runtime"),
            "binary_format_metadata": {
                "elf_machine": backend.get("elf_machine"),
                "elf_class": backend.get("elf_class"),
                "pe_machine": backend.get("pe_machine", []),
            },
            "execution_status": backend.get("execution", "provider-required"),
            "conformance_status": "not-established-by-catalogue",
        })
    return {
        "schema": "CHM-ISA-CROSS-PLATFORM-CROSSWALK-1",
        "sources": [str(ISA.relative_to(ROOT)), str(BACKENDS.relative_to(ROOT))],
        "architecture_records": len(rows),
        "instruction_form_records": sum(len(x["instruction_rows"]) for x in rows),
        "policy": "Compiler target availability, binary-format recognition, emulation and native conformance are distinct states.",
        "architectures": rows,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = {
        "schema": "CHM-CROSS-PLATFORM-REFERENCE-1",
        "commands": command_crosswalk(),
        "isa": isa_crosswalk(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"commands={result['commands']['unique_command_names']} "
          f"architectures={result['isa']['architecture_records']} "
          f"instruction_forms={result['isa']['instruction_form_records']} "
          f"output={args.output}")

if __name__ == "__main__":
    main()
