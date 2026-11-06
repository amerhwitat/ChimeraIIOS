#!/usr/bin/env bash
# Verify the actual terminal/shell executables inside a Linux live rootfs.
# This reports package presence and smoke tests; it does not claim Koronos ABI support.
set -Eeuo pipefail
ROOTFS="${1:?usage: verify-terminal-shell-suite.sh ROOTFS [target-arch]}"
TARGET_ARCH="${2:-x86_64}"
OUT="$ROOTFS/usr/share/chimera/aurora/terminal-shell-staging.json"
mkdir -p "$(dirname "$OUT")" "$ROOTFS/usr/share/applications"
python3 - "$ROOTFS" "$TARGET_ARCH" "$OUT" <<'PY'
import hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]); target=sys.argv[2]; output=pathlib.Path(sys.argv[3])
rows=[
 ("bash","shell","bash"),("zsh","shell","zsh"),("fish","shell","fish"),("dash","shell","dash"),
 ("mksh","shell","mksh"),("yash","shell","yash"),("elvish","shell","elvish"),("nushell","shell","nu"),
 ("xterm","terminal","xterm"),("gnome-terminal","terminal","gnome-terminal"),("gnome-console","terminal","kgx"),("konsole","terminal","konsole"),
 ("xfce4-terminal","terminal","xfce4-terminal"),("foot","terminal","foot"),("kitty","terminal","kitty"),("ptyxis","terminal","ptyxis"),
 ("alacritty","terminal","alacritty"),("wezterm","terminal","wezterm"),("ghostty","terminal","ghostty"),("contour","terminal","contour"),
 ("terminator","terminal","terminator"),("tilix","terminal","tilix"),("mate-terminal","terminal","mate-terminal"),("qterminal","terminal","qterminal"),
 ("sakura","terminal","sakura"),("terminology","terminal","terminology"),("lxterminal","terminal","lxterminal"),("blackbox-terminal","terminal","blackbox")]
machines={"x86_64":"Advanced Micro Devices X86-64","amd64":"Advanced Micro Devices X86-64",
 "aarch64":"AArch64","arm64":"AArch64","i686":"Intel 80386","i386":"Intel 80386",
 "riscv64":"RISC-V","ppc64le":"PowerPC64","s390x":"IBM S/390"}
expected=machines.get(target,target); entries=[]
for ident,kind,binary in rows:
    path=next((p for p in (root/"usr/local/bin"/binary,root/"usr/bin"/binary,root/"bin"/binary) if p.is_file() and p.stat().st_mode&0o111),None)
    row={"id":ident,"kind":kind,"binary":binary,"status":"unavailable","runtime_status":"not-runtime-tested","target_architecture":target}
    if path:
        row.update(path="/"+str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if path.read_bytes()[:4]==b"\x7fELF":
            r=subprocess.run(["readelf","-h",str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            machine=next((line.split(":",1)[1].strip() for line in r.stdout.splitlines() if line.strip().startswith("Machine:")),None)
            row["elf_machine"]=machine
            if not machine or (expected not in machine and machine not in expected): row["status"]="wrong-architecture"
            else:
                row["status"]="verified-elf-provider"
                if kind=="shell":
                    rel="/"+str(path.relative_to(root))
                    command=["chroot",str(root),rel,"-c","printf CHIMERA_SHELL_SMOKE"] if (root/"bin/sh").exists() else [str(path),"-c","printf CHIMERA_SHELL_SMOKE"]
                    probe=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
                    row["runtime_status"]="shell-command-smoke-pass" if probe.returncode==0 and b"CHIMERA_SHELL_SMOKE" in probe.stdout else "shell-command-smoke-fail"
                else:
                    rel="/"+str(path.relative_to(root))
                    command=["chroot",str(root),rel,"--version"] if (root/"bin/sh").exists() else [str(path),"--version"]
                    probe=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
                    row["runtime_status"]="version-smoke-pass" if probe.returncode==0 else "version-smoke-fail"
        else: row["status"]="present-but-not-ELF"
    entries.append(row)
manifest={"schema":"AURORA-TERMINAL-SHELL-STAGING-2","target_architecture":target,
 "policy":"Hashes and basic executable smoke tests only; this Linux image is not proof of Koronos syscall/ABI compatibility.","entries":entries}
output.write_text(json.dumps(manifest,indent=2)+"\n")
names={"xterm":"XTerm","gnome-terminal":"GNOME Terminal","gnome-console":"GNOME Console","konsole":"Konsole","xfce4-terminal":"XFCE Terminal",
       "foot":"Foot","kitty":"Kitty","ptyxis":"Ptyxis","alacritty":"Alacritty","wezterm":"WezTerm","ghostty":"Ghostty","contour":"Contour",
       "terminator":"Terminator","tilix":"Tilix","mate-terminal":"MATE Terminal","qterminal":"QTerminal",
       "sakura":"Sakura","terminology":"Terminology","lxterminal":"LXTerminal","blackbox-terminal":"Black Box Terminal"}
for row in entries:
    ident=row["id"]
    if row["kind"]=="terminal":
        desktop=root/"usr/share/applications"/f"chimera-terminal-{ident}.desktop"
        if row["status"]=="verified-elf-provider" and row["runtime_status"]=="version-smoke-pass":
            desktop.write_text("[Desktop Entry]\nType=Application\nName="+names.get(ident,ident)+"\nExec=/"+row["path"].lstrip("/")+
              "\nTerminal=false\nCategories=System;TerminalEmulator;\nX-Chimera-Aurora=true\n")
        else:
            desktop.unlink(missing_ok=True)
    elif row["kind"]=="shell":
        desktop=root/"usr/share/applications"/f"chimera-shell-{ident}.desktop"
        launcher=root/"usr/lib/chimera/aurora/launch-shell.sh"
        if row["status"]=="verified-elf-provider" and row["runtime_status"]=="shell-command-smoke-pass" and launcher.is_file():
            desktop.write_text("[Desktop Entry]\nType=Application\nName=Aurora Shell — "+ident+"\nExec=/usr/lib/chimera/aurora/launch-shell.sh "+ident+
              "\nTerminal=true\nCategories=System;TerminalEmulator;Development;\nX-Chimera-Aurora=true\n")
        else:
            desktop.unlink(missing_ok=True)
missing=[e["id"] for e in entries if e["status"]!="verified-elf-provider"]
bad=[e["id"] for e in entries if e["runtime_status"].endswith("-fail")]
print(f"[AURORA-TERMINALS] verified={len(entries)-len(missing)}/{len(entries)} missing_or_wrong_arch={','.join(missing) or 'none'} smoke_fail={','.join(bad) or 'none'}")
PY
if [[ "${CHIMERA_TERMINAL_REQUIRE_ALL:-0}" == "1" ]]; then
  python3 - "$OUT" <<'PY'
import json,sys
report=json.load(open(sys.argv[1],encoding="utf-8"))
failed=[row for row in report["entries"] if row["status"]!="verified-elf-provider" or row["runtime_status"] not in ("shell-command-smoke-pass","version-smoke-pass")]
if failed:
    raise SystemExit("terminal/shell acceptance failed: "+", ".join(f"{x['id']}={x['status']}/{x['runtime_status']}" for x in failed))
print("All 20 terminals and 8 shells passed ELF and executable smoke checks.")
PY
fi
