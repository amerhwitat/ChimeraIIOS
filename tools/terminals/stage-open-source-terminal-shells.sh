#!/usr/bin/env bash
# Stage real open-source shells and terminal emulators into an ISO rootfs.
# APT verifies repository metadata/signatures; dependency packages are extracted
# into the target rootfs without installing them on the build host.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR must point at the target rootfs}"
WORK="${CHIMERA_TERMINAL_PACKAGE_WORK:-${CHIMERA_BUILD_DIR:-$ROOT/build}/terminal-packages}"
REQUIRE_ALL="${CHIMERA_TERMINAL_REQUIRE_ALL:-0}"
mkdir -p "$WORK/archives" "$WORK/extracted" "$DEST/usr/bin" "$DEST/usr/share/chimera/aurora"
for tool in apt-get apt-cache dpkg-deb python3 readelf; do
  command -v "$tool" >/dev/null 2>&1 || { echo "[AURORA-TERMINALS] required staging tool missing: $tool" >&2; exit 1; }
done
declare -A PACKAGE_BIN=(
  [bash]=bash [zsh]=zsh [fish]=fish [dash]=dash [mksh]=mksh
  [yash]=yash [elvish]=elvish [nushell]=nu
  [xterm]=xterm [gnome-terminal]=gnome-terminal [konsole]=konsole
  [xfce4-terminal]=xfce4-terminal [foot]=foot [kitty]=kitty
  [alacritty]=alacritty [wezterm]=wezterm [ghostty]=ghostty [contour]=contour
)
declare -A APT_PACKAGE=(
  [bash]=bash [zsh]=zsh [fish]=fish [dash]=dash [mksh]=mksh
  [yash]=yash [elvish]=elvish [nushell]=nushell
  [xterm]=xterm [gnome-terminal]=gnome-terminal [konsole]=konsole
  [xfce4-terminal]=xfce4-terminal [foot]=foot [kitty]=kitty
  [alacritty]=alacritty [wezterm]=wezterm [ghostty]=ghostty [contour]=contour
)
echo "[AURORA-TERMINALS] Updating signed APT metadata"
apt-get update -o Acquire::Retries=5
AVAILABLE=()
for id in "${!APT_PACKAGE[@]}"; do
  pkg="${APT_PACKAGE[$id]}"
  candidate="$(apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2; exit}' || true)"
  if [[ -n "$candidate" && "$candidate" != "(none)" ]]; then
    AVAILABLE+=("$pkg")
  else
    echo "[AURORA-TERMINALS] no signed distro package candidate for $id ($pkg); source build required"
  fi
done
if (("${#AVAILABLE[@]}")); then
  apt-get install --download-only --reinstall --no-install-recommends -y \
    -o "Dir::Cache::archives=$WORK/archives" "${AVAILABLE[@]}"
  for deb in "$WORK"/archives/*.deb; do
    [[ -f "$deb" ]] || continue
    dpkg-deb -x "$deb" "$WORK/extracted"
  done
  # Never overwrite a source-built executable with a package copy; still stage
  # its package libraries, resources, desktop files and other dependencies.
  cp -an "$WORK/extracted/." "$DEST/"
fi
python3 - "$DEST" "$REQUIRE_ALL" "${CHIMERA_TARGET_ARCH:-$(uname -m)}" <<'PY'
import hashlib,json,pathlib,shutil,subprocess,sys
dest=pathlib.Path(sys.argv[1]); require_all=sys.argv[2]=="1"; target=sys.argv[3]; readelf=shutil.which("readelf")\nmachines={"x86_64":"Advanced Micro Devices X86-64","amd64":"Advanced Micro Devices X86-64","aarch64":"AArch64","arm64":"AArch64","i686":"Intel 80386","i386":"Intel 80386","riscv64":"RISC-V","ppc64le":"PowerPC64","s390x":"IBM S/390"}\nexpected=machines.get(target,target)
rows=[
 ("bash","shell","bash"),("zsh","shell","zsh"),("fish","shell","fish"),("dash","shell","dash"),
 ("mksh","shell","mksh"),("yash","shell","yash"),("elvish","shell","elvish"),("nushell","shell","nu"),
 ("xterm","terminal","xterm"),("gnome-terminal","terminal","gnome-terminal"),("konsole","terminal","konsole"),
 ("xfce4-terminal","terminal","xfce4-terminal"),("foot","terminal","foot"),("kitty","terminal","kitty"),
 ("alacritty","terminal","alacritty"),("wezterm","terminal","wezterm"),("ghostty","terminal","ghostty"),
 ("contour","terminal","contour")]
manifest=[]
for ident,kind,binary in rows:
    candidates=[dest/"usr/bin"/binary,dest/"bin"/binary]
    path=next((p for p in candidates if p.is_file() and p.stat().st_mode&0o111),None)
    row={"id":ident,"kind":kind,"binary":binary,"status":"unavailable","runtime_status":"not-runtime-tested"}
    if path:
        row.update(status="binary-present",path="/"+str(path.relative_to(dest)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if readelf:
            proc=subprocess.run([readelf,"-h",str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            machine=next((x.split(":",1)[1].strip() for x in proc.stdout.splitlines() if x.strip().startswith("Machine:")),None)
            if proc.returncode or not machine: row["status"]="present-but-not-valid-ELF"
            elif expected not in machine and machine not in expected: row["status"]="wrong-architecture"\n            else: row["elf_machine"]=machine
        else: row["status"]="present-hash-only"
    manifest.append(row)
out={"schema":"AURORA-TERMINAL-SHELL-STAGING-1","policy":"Only real executable files are listed; SHA-256 identifies exact bytes; staging does not imply runtime compatibility.","entries":manifest}
p=dest/"usr/share/chimera/aurora/terminal-shell-staging.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n")
missing=[r["id"] for r in manifest if r["status"]!="binary-present"]
print(f"[AURORA-TERMINALS] staged={len(manifest)-len(missing)}/{len(manifest)} missing={','.join(missing) if missing else 'none'}")
if require_all and missing: raise SystemExit("required terminal/shell binaries missing: "+", ".join(missing))
PY
