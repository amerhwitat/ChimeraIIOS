#!/usr/bin/env python3
"""Resolve missing Linux catalogue commands to real Debian package binaries.

This tool never creates placeholder executables or aliases. A command is marked
provided only after an executable is visible in PATH inside the target rootfs.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BUILTINS = set("""alias bg break builtin caller case cd command continue declare dirs echo eval exec exit export fc fg for function getopts hash help history if jobs let local logout mapfile popd printf pushd read readarray readonly return select set shift shopt source suspend test times trap type ulimit umask unalias unset until wait while""".split())
SEARCH_DIRS = {"/bin", "/usr/bin", "/sbin", "/usr/sbin", "/usr/games"}

def run(args: list[str], *, capture: bool = False):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--ss64", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--require-all", action="store_true",
                     help="fail when any executable Linux catalogue command has no verified provider")
    args = ap.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    raw = catalog.get("linux_bash", [])
    discovered = {(x.get("name") if isinstance(x, dict) else x).strip()
                  for x in raw if isinstance(x, (str, dict)) and
                  (x.get("name") if isinstance(x, dict) else x)}
    if args.ss64 and args.ss64.is_file():
        try:
            ss64 = json.loads(args.ss64.read_text(encoding="utf-8"))
            # SS64's Linux section also indexes syntax articles, examples,
            # headings and aliases. Treat only executable command pages (or
            # aliases already known as shell builtins/real commands) as commands.
            known_aliases = {"gawk", "ifdown", "pgrep", "readarray", "unalias", "unix2dos", "uudecode"}
            for item in ss64.get("platforms", {}).get("linux_bash", {}).get("commands", []):
                name = item.get("name") if isinstance(item, dict) else item
                source = item.get("source", "") if isinstance(item, dict) else ""
                if not isinstance(name, str):
                    continue
                token = name.strip()
                if not re.fullmatch(r"[A-Za-z0-9_.+-]+", token):
                    continue
                page = source.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
                page = re.sub(r"\.html?$", "", page, flags=re.IGNORECASE).lower()
                normalized = token.lower()
                if not page or page.startswith("syntax-") or normalized == "rem":
                    continue
                if page == normalized or normalized in BUILTINS or normalized in known_aliases or shutil.which(normalized):
                    discovered.add(normalized)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: could not read SS64 Linux command index: {exc}")
    names = sorted(discovered)
    rows: dict[str, dict] = {}
    missing: list[str] = []
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9_.+-]+", name):
            rows[name] = {"status": "shell-syntax-or-non-executable-catalogue-token"}
            continue
        # Prefer an actual executable provider when one exists (for example
        # /usr/bin/printf), while still recognizing syntax/builtins that have
        # no standalone executable (for example case, cd and eval).
        path = shutil.which(name)
        if path:
            rows[name] = {"status": "existing-executable-provider", "path": path}
        elif name in BUILTINS:
            rows[name] = {"status": "provided-by-shell-builtin"}
        else:
            rows[name] = {"status": "provider-not-found-yet"}
            missing.append(name)

    package_candidates: dict[str, list[str]] = {name: [] for name in missing}
    if missing and not args.no_install:
        if not shutil.which("apt-file"):
            run(["apt-get", "update", "-qq"])
            installed = run(["apt-get", "install", "-y", "--no-install-recommends", "apt-file"])
            if installed.returncode:
                print("apt-file could not be installed; unresolved commands remain reported.")
        if shutil.which("apt-file"):
            update = run(["apt-file", "update"])
            if update.returncode:
                print("apt-file index update failed; unresolved commands remain reported.")
            else:
                for start in range(0, len(missing), 35):
                    chunk = missing[start:start + 35]
                    alternation = "|".join(re.escape(x) for x in chunk)
                    pattern = rf"(^|/)(usr/)?(s?bin|games)/({alternation})$"
                    found = run(["apt-file", "search", "-x", pattern], capture=True)
                    if found.returncode not in (0, 1):
                        continue
                    for line in (found.stdout or "").splitlines():
                        if ": " not in line:
                            continue
                        package, filename = line.split(": ", 1)
                        command = Path(filename).name
                        if command not in package_candidates:
                            continue
                        parent = "/" + str(Path(filename).parent).lstrip("/")
                        if parent not in SEARCH_DIRS:
                            continue
                        package = package.split(":", 1)[0]
                        if package and package not in package_candidates[command]:
                            package_candidates[command].append(package)

    if not args.no_install:
        attempted: set[str] = set()
        for name in missing:
            for package in package_candidates.get(name, []):
                if package not in attempted:
                    result = run(["apt-get", "install", "-y", "--no-install-recommends", package])
                    attempted.add(package)
                else:
                    result = None
                path = shutil.which(name)
                if path:
                    rows[name] = {"status": "verified-package-provider-installed",
                                  "package": package, "path": path}
                    break
            else:
                candidates = package_candidates.get(name, [])
                rows[name] = {
                    "status": "no-package-provider-found" if not candidates else "package-install-did-not-provide-command",
                    "candidate_packages": candidates,
                }

    # Package installation may create alternatives or dependencies that
    # satisfy commands processed earlier (for example /usr/bin/open from
    # xdg-utils). Re-scan every unresolved name after the complete install pass.
    for name in missing:
        path = shutil.which(name)
        if path:
            previous = rows[name]
            rows[name] = {
                "status": "verified-provider-after-package-install",
                "path": path,
                "candidate_packages": previous.get("candidate_packages", []),
            }

    counts: dict[str, int] = {}
    for row in rows.values():
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    report = {
        "schema": "CHIMERA-LINUX-CATALOGUE-PROVIDERS-1",
        "catalogue": str(args.catalog),
        "command_count": len(names),
        "policy": "Only shell builtins or real executable files resolved in PATH are counted as providers. No placeholder binaries are generated. This verifies Debian/Linux userspace providers, not Koronos-native syscall compatibility.",
        "counts": counts,
        "commands": [{"name": name, **rows[name]} for name in names],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"command_count": len(names), "counts": counts}, sort_keys=True))
    unresolved = [name for name, row in rows.items()
                  if row["status"] in ("provider-not-found-yet",
                                       "no-package-provider-found",
                                       "package-install-did-not-provide-command")]
    if args.require_all and unresolved:
        print("unresolved Linux command providers: " + ", ".join(unresolved), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
