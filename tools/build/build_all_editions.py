#!/usr/bin/env python3
"""Build all Chimera II OS editions/configurations with CMake.

This is a build orchestrator, not a cross-compiler. Toolchains must already
exist or be supplied with CMAKE_TOOLCHAIN_FILE. Failed configurations are
reported and do not get mislabeled as successful artifacts.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess
from pathlib import Path
EDITIONS=["desktop","server","mobile","edge","iot","cvel"]
ARCHES=["x86_64","arm64","riscv64"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",default="."); ap.add_argument("--build-root",default="build/editions"); ap.add_argument("--generator",default="Ninja"); ap.add_argument("--edition",action="append"); ap.add_argument("--arch",action="append"); ap.add_argument("--install",action="store_true"); args=ap.parse_args()
    src=Path(args.source).resolve(); root=Path(args.build_root); editions=args.edition or EDITIONS; arches=args.arch or ["native"]
    cmake=shutil.which("cmake");
    if not cmake: raise SystemExit("cmake not found")
    results=[]
    for edition in editions:
        for arch in arches:
            b=root/f"{edition}-{arch}"; b.mkdir(parents=True,exist_ok=True)
            cfg=[cmake,"-S",str(src),"-B",str(b),"-DCHIMERA_EDITION="+edition]
            if arch!="native": cfg.append("-DCHIMERA_TARGET_ARCH="+arch)
            try:
                subprocess.run(cfg,check=True)
                subprocess.run([cmake,"--build",str(b),"--parallel"],check=True)
                if args.install: subprocess.run([cmake,"--install",str(b),"--prefix",str(b/"stage")],check=True)
                results.append({"edition":edition,"arch":arch,"status":"success","build_dir":str(b)})
            except subprocess.CalledProcessError as e:
                results.append({"edition":edition,"arch":arch,"status":"failed","returncode":e.returncode,"build_dir":str(b)})
    out=root/"build-matrix.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({"schema":"CHIMERA-BUILD-MATRIX-1","results":results},indent=2))
    print(out)
    return 0 if all(x["status"]=="success" for x in results) else 2
if __name__=="__main__": raise SystemExit(main())
