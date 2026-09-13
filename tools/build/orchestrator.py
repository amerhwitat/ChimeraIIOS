"""Unified, safe build/dependency/package orchestration for Chimera II OS."""
from __future__ import annotations
import argparse, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("build_manifest.json")

def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def which(name: str):
    return shutil.which(name)

def run(cmd, root=ROOT, dry_run=False):
    cmd = [str(x) for x in cmd]
    print("[chimera] $ " + " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.run(cmd, cwd=root).returncode

def probe(name: str):
    p = which(name)
    return {"tool": name, "path": p, "available": bool(p)}

def doctor():
    m = load_manifest()
    tools = ["cmake", "ctest", "cpack", "python", "cargo", "rustc", "node", "npm", "java", "dotnet", "kotlinc", "swift", "dart", "nasm"]
    result = {"platform": platform.platform(), "machine": platform.machine(), "tools": [probe(t) for t in tools]}
    print(json.dumps(result, indent=2))
    return 0

def configure(build: Path, generator=None, dry_run=False):
    cmd = [which("cmake") or "cmake", "-S", ROOT, "-B", build, "-DCHIMERA_ENABLE_EXPERIMENTAL=ON"]
    if generator:
        cmd += ["-G", generator]
    return run(cmd, dry_run=dry_run)

def native_build(build: Path, jobs=None, dry_run=False):
    cmd = [which("cmake") or "cmake", "--build", build, "--config", "Release"]
    if jobs:
        cmd += ["--parallel", str(jobs)]
    else:
        cmd += ["--parallel"]
    return run(cmd, dry_run=dry_run)

def native_test(build: Path, dry_run=False):
    return run([which("ctest") or "ctest", "--test-dir", build, "--output-on-failure", "-C", "Release"], dry_run=dry_run)

def native_package(build: Path, dry_run=False):
    return run([which("cpack") or "cpack", "--config", build / "CPackConfig.cmake", "-C", "Release"], dry_run=dry_run)

def install_deps(dry_run=False):
    """Install only project-declared dependencies using trusted package managers."""
    commands = []
    if (ROOT / "requirements.txt").exists(): commands.append([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if (ROOT / "pyproject.toml").exists(): commands.append([sys.executable, "-m", "pip", "install", "-e", "."])
    if (ROOT / "Cargo.toml").exists() and which("cargo"): commands.append(["cargo", "fetch", "--locked"] if (ROOT / "Cargo.lock").exists() else ["cargo", "fetch"])
    if (ROOT / "package-lock.json").exists(): commands.append(["npm", "ci"])
    elif (ROOT / "package.json").exists(): commands.append(["npm", "install"])
    if (ROOT / "pom.xml").exists() and which("mvn"): commands.append(["mvn", "-B", "dependency:go-offline"])
    if (ROOT / "build.gradle" ).exists() and which("gradle"): commands.append(["gradle", "dependencies"])
    if (ROOT / "build.gradle.kts" ).exists() and which("gradle"): commands.append(["gradle", "dependencies"])
    if (ROOT / "package.json").exists() and not which("npm"):
        print("npm is required for the Node/TypeScript tree", file=sys.stderr); return 127
    for cmd in commands:
        rc = run(cmd, dry_run=dry_run)
        if rc: return rc
    print(f"[chimera] dependency steps: {len(commands)}")
    return 0

def clean(build: Path):
    if build.exists():
        shutil.rmtree(build)
    print(f"[chimera] removed {build}")
    return 0

def main(argv=None):
    ap = argparse.ArgumentParser(description="Chimera II OS unified build/install automation")
    ap.add_argument("command", choices=["doctor", "deps", "configure", "build", "test", "package", "install", "clean", "all"])
    ap.add_argument("--build-dir", default=str(ROOT / "build"))
    ap.add_argument("--generator")
    ap.add_argument("--jobs", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    build = Path(args.build_dir).resolve()
    if args.command == "doctor": return doctor()
    if args.command == "deps": return install_deps(args.dry_run)
    if args.command == "clean": return clean(build)
    if args.command == "configure": return configure(build, args.generator, args.dry_run)
    if args.command == "build":
        if not args.dry_run and not (build / "CMakeCache.txt").exists():
            rc = configure(build, args.generator); 
            if rc: return rc
        return native_build(build, args.jobs, args.dry_run)
    if args.command == "test": return native_test(build, args.dry_run)
    if args.command == "package": return native_package(build, args.dry_run)
    if args.command == "install":
        prefix = build / "install"
        return run([which("cmake") or "cmake", "--install", build, "--config", "Release", "--prefix", prefix], dry_run=args.dry_run)
    # all
    for fn in (lambda: install_deps(args.dry_run), lambda: configure(build, args.generator, args.dry_run), lambda: native_build(build, args.jobs, args.dry_run), lambda: native_test(build, args.dry_run), lambda: native_package(build, args.dry_run)):
        rc = fn()
        if rc: return rc
    return 0

if __name__ == "__main__": raise SystemExit(main())
