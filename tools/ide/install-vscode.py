#!/usr/bin/env python3
"""Install Microsoft's Visual Studio Code through an official host package manager."""
import argparse, platform, shutil, subprocess, sys

def install_plan(system, which=shutil.which):
    if system == "Linux":
        if which("flatpak"): return ["flatpak","install","--user","--noninteractive","flathub","com.visualstudio.code"]
        if which("snap"): return ["sudo","snap","install","code","--classic"]
        raise RuntimeError("Install Flatpak or Snap from your distribution, then rerun; no unverified archive is downloaded.")
    if system == "Windows":
        if not which("winget"): raise RuntimeError("Install Windows App Installer/winget first.")
        return ["winget","install","--id","Microsoft.VisualStudioCode","--exact","--source","winget","--accept-package-agreements","--accept-source-agreements"]
    if system == "Darwin":
        if not which("brew"): raise RuntimeError("Install Homebrew first.")
        return ["brew","install","--cask","visual-studio-code"]
    raise RuntimeError(f"unsupported host OS: {system}")

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--install",action="store_true")
    a=p.parse_args()
    try: cmd=install_plan(platform.system())
    except RuntimeError as exc: print(f"vscode: {exc}",file=sys.stderr); return 2
    print("Install plan:", " ".join(cmd))
    if not a.install: print("Dry run only; pass --install to proceed."); return 0
    result=subprocess.run(cmd,check=False)
    if result.returncode: print(f"vscode: package manager exited {result.returncode}",file=sys.stderr)
    return result.returncode
if __name__=="__main__": raise SystemExit(main())
