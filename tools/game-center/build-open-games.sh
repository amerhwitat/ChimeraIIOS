#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/web/game-center-manifest.json"; SRC="$ROOT/.local/games-src"; BIN="$ROOT/.local/games"; mkdir -p "$SRC" "$BIN"
command -v git >/dev/null || { echo "git is required"; exit 1; }
python3 - "$MANIFEST" "$SRC" "$BIN" <<'PY'
import json,os,subprocess,sys
manifest,src,binroot=sys.argv[1:]
for x in json.load(open(manifest,encoding="utf-8"))["games"]:
 gid,title,genre,license,multi,mode,repo,site=x; d=os.path.join(src,gid); print("\n==",title,"==")
 if not os.path.isdir(os.path.join(d,".git")): subprocess.run(["git","clone","--depth","1",repo,d],check=False)
 if not os.path.isdir(d): print("SKIP: clone failed"); continue
 if os.path.exists(os.path.join(d,"CMakeLists.txt")): cmds=[["cmake","-S",d,"-B",os.path.join(d,"build"),"-DCMAKE_BUILD_TYPE=Release"],["cmake","--build",os.path.join(d,"build"),"-j"]]
 elif os.path.exists(os.path.join(d,"meson.build")): cmds=[["meson","setup",os.path.join(d,"build"),d,"--buildtype=release"],["meson","compile","-C",os.path.join(d,"build")]]
 elif os.path.exists(os.path.join(d,"Cargo.toml")): cmds=[["cargo","build","--release","--manifest-path",os.path.join(d,"Cargo.toml")]]
 elif os.path.exists(os.path.join(d,"configure")): cmds=[["bash",os.path.join(d,"configure"),"--prefix="+os.path.join(d,"install")],["make","-C",d,"-j"],["make","-C",d,"install"]]
 else: print("SKIP: unsupported build system"); continue
 ok=True
 for cmd in cmds:
  print("+"," ".join(cmd))
  if subprocess.run(cmd).returncode: ok=False; break
 if ok:
  open(os.path.join(binroot,gid+".path"),"w").write(d+"\n")
  print("BUILT:",gid,"source:",d)
 else: print("BUILD FAILED:",gid)
print("\nBuild pass complete. Native binaries remain local.")
PY
