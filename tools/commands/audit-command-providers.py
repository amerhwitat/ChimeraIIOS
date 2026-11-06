#!/usr/bin/env python3
"""Produce per-entry command-provider evidence without inventing executables or conflating Linux ELF with the Koronos ABI."""
from __future__ import annotations
import argparse,json,shutil,subprocess
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--rootfs",type=Path,required=True);ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument("--native-matrix",dest="linux_abi_matrix",type=Path);ap.add_argument("--output",type=Path);a=ap.parse_args()
    root=a.rootfs.resolve();cat=json.loads((a.repo/"system/commands/chimera-command-list.json").read_text())
    matrix={}
    if a.linux_abi_matrix and a.linux_abi_matrix.exists():
        try:
            m=json.loads(a.linux_abi_matrix.read_text())
            for t in m.get("targets",[]):
                if t.get("binary_status")=="linux-abi-cross-compiled-and-elf-machine-validated":
                    for alias in t.get("aliases",[]): matrix.setdefault(alias,[]).append({"target":t["target"],"runtime_status":t.get("runtime_status")})
        except (OSError,json.JSONDecodeError): pass
    bash=root/"bin/bash"
    if not bash.exists(): bash=root/"usr/bin/bash"
    def linux_provider(name):
        if bash.exists() and shutil.which("chroot"):
            try:
                p=subprocess.run(["chroot",str(root),str(bash.relative_to(root) if bash.is_relative_to(root) else "/bin/bash"),"-c",'type -t -- "$1" >/dev/null 2>&1',"_",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
                if p.returncode==0:return "bash-builtin-or-command"
            except (OSError,subprocess.TimeoutExpired): pass
        for d in ("bin","usr/bin","sbin","usr/sbin","usr/local/bin","usr/local/sbin","usr/lib/chimera/busybox-bin"):
            p=root/d/name
            if p.exists() and p.is_file() and p.stat().st_mode & 0o111:return "executable-present"
        return None
    namespaces={}
    for ns in ("linux_bash","macos_core","windows_cmd_core","powershell_core","vbscript_core","sql_server_core","native_chimera"):
        names=cat.get(ns,[]); rows=[]
        for name in names:
            provider=None;status="provider-missing"
            if ns=="linux_bash":
                provider=linux_provider(name);status="provider-present-not-command-runtime-tested" if provider else status
            elif ns=="macos_core": status="foreign-darwin-runtime-not-available"
            elif ns=="windows_cmd_core":
                status="wine-runtime-present-command-coverage-not-tested" if any((root/d/x).exists() for d in ("usr/bin","usr/local/bin") for x in ("wine","wine64")) else "windows-cmd-runtime-not-available"
            elif ns=="powershell_core":
                status="powershell-provider-present-not-command-tested" if any((root/d/"pwsh").exists() for d in ("usr/bin","usr/local/bin")) else "powershell-runtime-not-available"
            elif ns=="vbscript_core":
                status="wine-vbscript-host-unverified" if any((root/d/x).exists() for d in ("usr/bin","usr/local/bin") for x in ("wine","wine64")) else "vbscript-host-not-available"
            elif ns=="sql_server_core":
                status="sql-server-engine-not-available"
            elif ns=="native_chimera":
                if name in matrix:
                    provider="linux-abi-cross-built-multicall"
                    status="linux-abi-cross-built-not-koronos-native-runtime-not-tested"
            rows.append({"command":name,"status":status,"provider":provider,"linux_abi_targets":matrix.get(name,[])})
        namespaces[ns]={"catalogued":len(names),"provider_present":sum(bool(x["provider"]) for x in rows),"rows":rows}
    unique=set()
    for ns in namespaces.values():
        for row in ns["rows"]: unique.add(row["command"].casefold())
    result={"schema":"CHM-COMMAND-PROVIDER-AUDIT-1","unique_command_names":len(unique),"catalogue_entries":sum(x["catalogued"] for x in namespaces.values()),"namespaces":namespaces,"policy":"Presence and cross-build status are not runtime acceptance. Missing providers remain explicit; no placeholder executables are created."}
    out=a.output or root/"usr/share/chimera/catalogs/command-provider-audit.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"unique_command_names":result["unique_command_names"],"namespaces":{k:{x:y for x,y in v.items() if x!="rows"} for k,v in namespaces.items()}},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
