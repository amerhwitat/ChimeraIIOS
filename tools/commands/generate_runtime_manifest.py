#!/usr/bin/env python3
"""Build an auditable native/shell/compatibility capability manifest for catalogued commands."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "system" / "commands" / "chimera-command-list.json"
SS64 = ROOT / "system" / "commands" / "ss64-command-catalog.json"
ARABIC = ROOT / "system" / "commands" / "ss64-command-catalog.ar.json"
OUT = ROOT / "system" / "commands" / "command-runtime-capabilities.json"
REGISTRY = ROOT / "tools" / "commands" / "os-command-runtime.json"
NATIVE = {"pwd","echo","ls","cp","mv","touch","mkdir","rm","cat","clear","whoami","hostname","date","true","false","rmdir","ln","readlink","basename","dirname","uname","wc","head","tail","sleep"}
SHELL = set("""alias bg break builtin caller case cd command continue declare dirs eval exec exit export fc fg for function getopts hash help history if jobs let local logout mapfile popd printf pushd read readarray readonly return select set shift shopt source suspend test times trap type ulimit umask unalias unset until wait while""".split())
PLATFORM_ARRAYS = {
    "linux_bash":"linux_bash", "macos":"macos_core", "windows_cmd":"windows_cmd_core",
    "powershell":"powershell_core", "vbscript":"vbscript_core", "sql_server":"sql_server_core",
    "chimera_native":"native_chimera"
}
def names(value):
    for item in value if isinstance(value, list) else []:
        if isinstance(item, str) and item.strip():
            yield item.strip()
        elif isinstance(item, dict) and item.get("name"):
            yield str(item["name"]).strip()
def catalogue_kind(name, platforms, source_urls):
    """Separate executable commands from language tokens, syntax and API members."""
    value = str(name).strip()
    identifier = bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", value))
    urls = " ".join(str(u).casefold() for u in source_urls)
    if "sql_server" in platforms or "access" in platforms:
        return "language-feature"
    if "vbscript" in platforms and (value.startswith(".") or not identifier):
        return "language-feature"
    if "powershell" in platforms and (value.startswith("$") or value.startswith("-") or "syntax" in urls):
        return "language-feature"
    if "windows_cmd" in platforms and (not identifier or any(token in value for token in ("%","&&","||","::"))):
        return "shell-syntax"
    if "linux_bash" in platforms and ("syntax" in urls or value.startswith(".") or value.isdigit()):
        return "shell-syntax"
    if not identifier and any(token in platforms for token in ("linux_bash","macos","windows_cmd","powershell")):
        return "language-feature"
    return "executable-command"

def main():
    source=json.loads(BASE.read_text(encoding="utf-8"))
    rows={}
    for platform,key in PLATFORM_ARRAYS.items():
        for name in names(source.get(key, [])):
            norm=name.casefold()
            row=rows.setdefault(norm,{"name":name,"platforms":[],"source_urls":[]})
            if platform not in row["platforms"]: row["platforms"].append(platform)
    # The native multicall contract is authoritative even when a catalog is
    # incomplete or a refresh temporarily drops one of these entries.
    for name in sorted(NATIVE):
        norm=name.casefold()
        row=rows.setdefault(norm,{"name":name,"platforms":[],"source_urls":[]})
        if "chimera_native" not in row["platforms"]:
            row["platforms"].append("chimera_native")
    if SS64.exists():
        try:
            ss64=json.loads(SS64.read_text(encoding="utf-8"))
            for platform,data in ss64.get("platforms",{}).items():
                for item in data.get("commands",[]):
                    name=str(item.get("name","")).strip()
                    if not name: continue
                    norm=name.casefold()
                    row=rows.setdefault(norm,{"name":name,"platforms":[],"source_urls":[]})
                    if platform not in row["platforms"]: row["platforms"].append(platform)
                    url=item.get("source")
                    if url and url not in row["source_urls"]: row["source_urls"].append(url)
        except (OSError,json.JSONDecodeError) as exc:
            print(f"warning: ignoring invalid SS64 cache: {exc}")
    arabic={}
    if ARABIC.exists():
        try:
            arabic=json.loads(ARABIC.read_text(encoding="utf-8")).get("commands",{})
        except (OSError,json.JSONDecodeError):
            pass
    # Preserve the full previously Arabized name inventory even if the raw crawl
    # cache is absent or temporarily empty. Unknown platform ownership stays explicit.
    for key, value in arabic.items():
        name = str(value.get("name", key)) if isinstance(value, dict) else str(key)
        norm = name.casefold()
        row = rows.setdefault(norm, {"name": name, "platforms": [], "source_urls": []})
        if not row["platforms"]:
            row["platforms"].append("ss64-catalog")
    registry_modes={}
    if REGISTRY.exists():
        try:
            registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
            for group, info in registry.get("providers", {}).items():
                for name in info.get("commands", []):
                    norm=str(name).casefold()
                    row=rows.setdefault(norm, {"name":str(name), "platforms":[], "source_urls":[]})
                    if group not in row["platforms"]: row["platforms"].append(group)
                    registry_modes[norm]=(info.get("mode","compatibility-provider-required"), info.get("runtime",group))
        except (OSError,json.JSONDecodeError) as exc:
            print(f"warning: ignoring invalid command runtime registry: {exc}")
    commands=[]
    for key,row in sorted(rows.items()):
        kind=catalogue_kind(row["name"], row["platforms"], row["source_urls"])
        if key in NATIVE: mode="native"; provider="chimera-cmd"
        elif key in SHELL: mode="shell-builtin"; provider="chimera-shell"
        elif kind in ("language-feature", "shell-syntax"):
            mode="language-feature"; provider="shell-interpreter-or-language-runtime"
        elif key in registry_modes:
            declared, runtime=registry_modes[key]
            # Only entries in NATIVE above are implemented by the compiled multicall.
            # Registry declarations describe a provider capability; they must not
            # silently promote dispatcher tools to native built-ins.
            mode="native-provider-required" if declared in ("native", "native-when-present") else declared
            provider=runtime
        else:
            mode="compatibility-provider-required"
            if any(p in row["platforms"] for p in ("windows_cmd","powershell","vbscript")):
                provider="windows-compat-runtime"
            elif any(p in row["platforms"] for p in ("linux_bash","macos")):
                provider="darwin-or-posix-provider"
            else:
                provider="platform-runtime-not-selected"
        label=arabic.get(key)
        if isinstance(label,dict): label=label.get("label")
        commands.append({
            "name":row["name"],"platforms":sorted(row["platforms"]),"mode":mode,
            "entry_kind":kind,
            "provider":provider,"arabic_label":label,
            "source_urls":sorted(set(row["source_urls"]))
        })
    OUT.write_text(json.dumps({
        "schema":"CHM-COMMAND-RUNTIME-CAPABILITIES-1",
        "policy":"Catalog presence does not mean a binary or implementation exists. Native entries are backed by src/chimera-command-compat/chimera-cmd.c and built as Linux userspace ELF aliases for the eight declared Linux ABIs. This does not imply Koronos syscall ABI compatibility; all other external commands require the named runtime/provider.",
        "native_binary":"rootfs/usr/lib/chimera/commands/linux-abi/<target>/chimera-cmd",
        "native_abi":"Linux userspace ELF; cross-built for eight Linux ABIs; not a Koronos syscall ABI",
        "native_alias_count":len(NATIVE),
        "koronos_abi_compatible":False,
        "command_count":len(commands),
        "executable_command_count":sum(c["entry_kind"]=="executable-command" for c in commands),
        "language_feature_count":sum(c["entry_kind"] in ("language-feature","shell-syntax") for c in commands),
        "shell_builtin_count":sum(c["mode"]=="shell-builtin" for c in commands),
        "mode_counts":{mode:sum(c["mode"]==mode for c in commands) for mode in sorted({c["mode"] for c in commands})},
        "commands":commands
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated command capability manifest: {len(commands)} commands")
if __name__=="__main__": main()
