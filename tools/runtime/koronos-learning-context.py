#!/usr/bin/env python3
"""Deterministic ISA/CPU/command context extractor for Koronos learning backends.

This is feature extraction, not a trained model. Catalog presence never proves execution.
"""
import argparse, json, platform, struct
from pathlib import Path

SCHEMA = "KORONOS-LEARNING-CONTEXT-1"
ALIASES = {"x86_64":"x86-64","amd64":"x86-64","x64":"x86-64","i386":"x86-32","i686":"x86-32","x86":"x86-32","aarch64":"armv9-a64","arm64":"armv9-a64","armv7l":"arm32","riscv64":"riscv64","riscv32":"riscv32"}

def read_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError: return {}
    except json.JSONDecodeError as exc: raise ValueError(f"{path}: invalid JSON: {exc}") from exc

def cpu_facts():
    model = platform.processor() or "unknown"; flags = set()
    if platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8",errors="replace").splitlines():
                k,sep,v=line.partition(":")
                if sep and k.strip().lower() in ("model name","hardware") and model=="unknown": model=v.strip()
                if sep and k.strip().lower() in ("flags","features"): flags.update(v.split())
        except OSError: pass
    return model, sorted(flags)

def rows(raw, fields):
    result=[]
    for row in raw if isinstance(raw,list) else []:
        if isinstance(row,dict): result.append(row)
        elif isinstance(row,(list,tuple)): result.append({fields[i]:row[i] for i in range(min(len(fields),len(row)))})
    return result

def build_context(root, mode="both"):
    if mode not in ("native","compatibility","both"): raise ValueError("mode must be native, compatibility, or both")
    root=Path(root)
    isa=read_json(root/"isa/isa_database.json")
    cmd=read_json(root/"system/commands/chimera-command-list.json")
    af=isa.get("architecture_row",["id","class","family","word_bits","status","encoding_model","source_ref","instruction_forms"])
    inf=isa.get("instruction_row",["architecture","mnemonic","form_id","operands","syntax","length_bits","value_bits","mask_bits"])
    archs=rows(isa.get("architectures"),af); ins=rows(isa.get("instructions"),inf)
    machine=platform.machine().lower(); host=ALIASES.get(machine,machine)
    model,flags=cpu_facts()
    native_doc=cmd.get("native_chimera",{})
    native=set(native_doc.get("commands",[])) if isinstance(native_doc,dict) else set()
    compatibility=set(cmd.get("compatibility_commands",[]))
    command_names=set(cmd.get("linux_bash",[])) if isinstance(cmd.get("linux_bash"),list) else set()
    if not compatibility: compatibility=command_names-native
    em=isa.get("execution_model",{}); hosted=em.get("hosted_compatibility_modes",{}) if isinstance(em,dict) else {}
    profiles=[]
    if mode in ("native","both"):
        profiles.append({"mode":"native","host_architecture":host,"host_pointer_bits":struct.calcsize("P")*8,"cpu_model":model,"cpu_flags":flags,
          "matching_instruction_forms":sum(host in str(i.get("architecture","")).lower() for i in ins),
          "candidate_architectures":sorted({str(a.get("id")) for a in archs if a.get("status") in ("verified","implemented","native")} | {host}),
          "commands":sorted(native),"command_count":len(native),
          "rule":"Only verified host/backend implementations are executable; catalog entries alone are not proof."})
    if mode in ("compatibility","both"):
        aliases=hosted.get("host_aliases",ALIASES) if isinstance(hosted,dict) else ALIASES
        profiles.append({"mode":"compatibility","candidate_architectures":sorted({str(a.get("id")) for a in archs if a.get("id")}),
          "architecture_aliases":aliases,"commands":sorted(compatibility),"command_count":len(compatibility),
          "execution_policy":hosted.get("candidate_execution_status","host-match-only; cross-ISA execution not implied") if isinstance(hosted,dict) else "provider-required",
          "rule":"Foreign execution requires a validated compatibility provider, ABI/runtime and backend; otherwise fail closed."})
    return {"schema":SCHEMA,"catalogs":{"isa_version":isa.get("version","missing"),"architecture_rows":len(archs),"instruction_forms":len(ins),
      "instruction_catalog_is_exhaustive":False,"command_registry_schema":cmd.get("schema_version","missing"),"unique_commands":len(native|compatibility|command_names)},
      "profiles":profiles,"learning_features":{
      "rnn_sequence":["event_type","time_delta","cpu_id","task_id","host_architecture","execution_mode","instruction_mnemonic","command","exit_code","fault_code"],
      "llm_context":["cpu_model","cpu_flags","host_architecture","execution_mode","isa_version","instruction_forms","command_mode","recent_events","recovery_history"],
      "offline_rl_state":["failure_class","service_state","heartbeat_age","restart_budget_remaining","host_architecture","execution_mode","provider_available","previous_verified_outcome"],
      "training_status":"feature extraction only; no trained RNN/LLM/RL weights are included"},
      "safety":{"catalog_presence_implies_execution":False,"cross_isa_without_provider":False,"model_may_execute_commands":False,"model_may_patch_kernel":False,"online_policy_mutation":False}}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--repo-root",default="."); p.add_argument("--mode",choices=("native","compatibility","both"),default="both"); p.add_argument("--output")
    a=p.parse_args()
    try:
        out=json.dumps(build_context(Path(a.repo_root).resolve(),a.mode),indent=2,ensure_ascii=False)+"\n"
        if a.output: Path(a.output).write_text(out,encoding="utf-8")
        else: print(out,end="")
        return 0
    except (OSError,ValueError) as exc: p.exit(2,f"koronos-learning-context: {exc}\n")
if __name__=="__main__": raise SystemExit(main())
