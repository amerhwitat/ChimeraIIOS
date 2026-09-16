#!/usr/bin/env python3
"""Chimera Cloud Fabric: safe discovery, plan generation and explicit execution."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "cloud" / "providers.json"


def registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def doctor(provider):
    data = registry()["providers"].get(provider)
    if not data:
        raise SystemExit(f"unknown provider: {provider}")
    commands = data.get("commands", [])
    print(f"provider={provider}")
    for command in commands:
        path = shutil.which(command)
        print(f"  {command}: {'installed ' + path if path else 'not-found'}")


def plan(provider, output):
    if provider not in registry()["providers"]:
        raise SystemExit(f"unknown provider: {provider}")
    payload = {
        "schema": "CHIMERA-PLAN-1",
        "provider": provider,
        "actions": ["validate", "provision", "configure", "verify"],
        "execution": "explicit-apply",
        "credentials": "external",
    }
    Path(output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"plan written: {output}")


def apply(provider, plan_file):
    plan_data = json.loads(Path(plan_file).read_text(encoding="utf-8"))
    if plan_data.get("provider") != provider:
        raise SystemExit("plan/provider mismatch")
    print(f"Refusing implicit infrastructure mutation for {provider}.")
    print("Use the provider-specific deployment application or CI job with explicit approval.")
    print(json.dumps(plan_data, indent=2))
    return 2


def main():
    parser = argparse.ArgumentParser(prog="chimera-cloud")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("providers")
    d = sub.add_parser("doctor"); d.add_argument("provider")
    p = sub.add_parser("plan"); p.add_argument("provider"); p.add_argument("--output", default="chimera-plan.json")
    a = sub.add_parser("apply"); a.add_argument("--provider", required=True); a.add_argument("--plan", required=True)
    args = parser.parse_args()
    if args.command == "providers":
        for name, info in registry()["providers"].items(): print(f"{name}: {info['kind']}")
    elif args.command == "doctor": doctor(args.provider)
    elif args.command == "plan": plan(args.provider, args.output)
    else: return apply(args.provider, args.plan)
    return 0

if __name__ == "__main__": sys.exit(main())
