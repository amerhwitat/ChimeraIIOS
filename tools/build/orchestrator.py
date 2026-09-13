"""Unified, safe build/dependency/package orchestration for Chimera II OS."""
from __future__ import annotations
import argparse, fnmatch, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("build_manifest.json")
SKIP_DIRS = {".git", "build", "target", "node_modules", ".venv", "venv", "dist", "out"}

def load_manifest(): return json.loads(MANIFEST.read_text(encoding="utf-8"))
def which(name: str): return shutil.which(name)
def run(cmd, root=ROOT, dry_run=False):
    cmd = [str(x) for x in cmd]; print("[chimera] $ " + " ".join(cmd))
    if dry_run: return 0
    return subprocess.run(cmd, cwd=root).returncode
def probe(name: str):
    p = which(name); return {"tool": name, "path": p, "available": bool(p)}
def find_files(*patterns):
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for pattern in patterns:
            found.extend(Path(base) / f for f in files if fnmatch.fnmatch(f, pattern))
    return sorted(set(found))
def doctor():
    tools = ["cmake", "ctest", "cpack", "python", "cargo", "rustc", "node", "npm", "java", "mvn", "gradle", "dotnet", "kotlinc", "swift", "dart", "nasm"]
    manifests = [str(p.relative_to(ROOT)) for p in find_files('Cargo.toml','package.json','pom.xml','build.gradle','build.gradle.kts','Package.swift','pubspec.yaml','*.csproj')]
    print(json.dumps({"platform": platform.platform(), "machine": platform.machine(), "tools": [probe(t) for t in tools], "manifests": manifests}, indent=2)); return 0
def configure(build: Path, generator=None, dry_run=False):
    cmd = [which("cmake") or "cmake", "-S", ROOT, "-B", build, "-DCHIMERA_ENABLE_EXPERIMENTAL=ON"]
    if generator: cmd += ["-G", generator]
    return run(cmd, dry_run=dry_run)
def native_build(build: Path, jobs=None, dry_run=False):
    cmd = [which("cmake") or "cmake", "--build", build, "--config", "Release", "--parallel"]
    if jobs: cmd.append(str(jobs))
    return run(cmd, dry_run=dry_run)
def native_test(build: Path, dry_run=False): return run([which("ctest") or "ctest", "--test-dir", build, "--output-on-failure", "-C", "Release"], dry_run=dry_run)
def native_package(build: Path, dry_run=False): return run([which("cpack") or "cpack", "--config", build / "CPackConfig.cmake", "-C", "Release"], dry_run=dry_run)
def project_commands():
    commands = []
    cargo = find_files("Cargo.toml")
    if cargo and which("cargo"):
        root = next((p.parent for p in cargo if (p.parent / "Cargo.lock").exists()), cargo[0].parent); locked = ["--locked"] if (root / "Cargo.lock").exists() else []
        commands += [("rust", root, ["cargo", "build", "--workspace", "--all-targets", *locked]), ("rust-test", root, ["cargo", "test", "--workspace", *locked])]
    for manifest in find_files("package.json"):
        if which("npm"):
            root = manifest.parent; commands += [("node", root, ["npm", "run", "build", "--if-present"]), ("node-test", root, ["npm", "test", "--if-present"])]
    for manifest in find_files("pom.xml"):
        if which("mvn"): commands += [("java", manifest.parent, ["mvn", "-B", "package"]), ("java-test", manifest.parent, ["mvn", "-B", "test"])]
    for manifest in find_files("build.gradle", "build.gradle.kts"):
        if which("gradle"): commands += [("gradle", manifest.parent, ["gradle", "build"]), ("gradle-test", manifest.parent, ["gradle", "test"])]
    for manifest in find_files("*.csproj"):
        if which("dotnet"): commands += [("dotnet", manifest.parent, ["dotnet", "build", manifest.name, "-c", "Release"]), ("dotnet-test", manifest.parent, ["dotnet", "test", manifest.name, "-c", "Release", "--no-build"])]
    for manifest in find_files("Package.swift"):
        if which("swift"): commands += [("swift", manifest.parent, ["swift", "build", "-c", "release"]), ("swift-test", manifest.parent, ["swift", "test"])]
    for manifest in find_files("pubspec.yaml"):
        if which("dart"): commands += [("dart", manifest.parent, ["dart", "pub", "get"]), ("dart-test", manifest.parent, ["dart", "test"])]
    return commands
def language_build(dry_run=False):
    for name, cwd, cmd in project_commands():
        if not name.endswith("-test"):
            rc = run(cmd, root=cwd, dry_run=dry_run)
            if rc: return rc
    return 0
def language_test(dry_run=False):
    for name, cwd, cmd in project_commands():
        if name.endswith("-test"):
            rc = run(cmd, root=cwd, dry_run=dry_run)
            if rc: return rc
    return 0
def install_deps(dry_run=False):
    commands = []
    if (ROOT / "requirements.txt").exists(): commands.append([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if (ROOT / "pyproject.toml").exists(): commands.append([sys.executable, "-m", "pip", "install", "-e", "."])
    cargo = find_files("Cargo.toml")
    if cargo and which("cargo"):
        p = next((p for p in cargo if (p.parent / "Cargo.lock").exists()), cargo[0]); commands.append(["cargo", "fetch", "--locked"] if (p.parent / "Cargo.lock").exists() else ["cargo", "fetch"])
    locks = find_files("package-lock.json")
    if locks: commands.append(["npm", "ci"])
    elif find_files("package.json"): commands.append(["npm", "install"])
    if (ROOT / "ChimeraIIOS.sln").exists() and which("dotnet"): commands.append(["dotnet", "restore", "ChimeraIIOS.sln"])
    for cmd in commands:
        rc = run(cmd, dry_run=dry_run)
        if rc: return rc
    print(f"[chimera] dependency steps: {len(commands)}"); return 0
def clean(build: Path):
    if build.exists(): shutil.rmtree(build)
    print(f"[chimera] removed {build}"); return 0
def main(argv=None):
    ap = argparse.ArgumentParser(description="Chimera II OS unified build/install automation")
    ap.add_argument("command", choices=["doctor", "deps", "configure", "build", "test", "package", "install", "clean", "all"]); ap.add_argument("--build-dir", default=str(ROOT / "build")); ap.add_argument("--generator"); ap.add_argument("--jobs", type=int); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv); build = Path(args.build_dir).resolve()
    if args.command == "doctor": return doctor()
    if args.command == "deps": return install_deps(args.dry_run)
    if args.command == "clean": return clean(build)
    if args.command == "configure": return configure(build, args.generator, args.dry_run)
    if args.command == "build":
        if not args.dry_run and not (build / "CMakeCache.txt").exists():
            rc = configure(build, args.generator)
            if rc: return rc
        rc = native_build(build, args.jobs, args.dry_run); return rc if rc else language_build(args.dry_run)
    if args.command == "test":
        rc = native_test(build, args.dry_run); return rc if rc else language_test(args.dry_run)
    if args.command == "package": return native_package(build, args.dry_run)
    if args.command == "install": return run([which("cmake") or "cmake", "--install", build, "--config", "Release", "--prefix", build / "install"], dry_run=args.dry_run)
    for fn in (lambda: install_deps(args.dry_run), lambda: configure(build, args.generator, args.dry_run), lambda: native_build(build, args.jobs, args.dry_run), lambda: language_build(args.dry_run), lambda: native_test(build, args.dry_run), lambda: language_test(args.dry_run), lambda: native_package(build, args.dry_run)):
        rc = fn()
        if rc: return rc
    return 0
if __name__ == "__main__": raise SystemExit(main())
