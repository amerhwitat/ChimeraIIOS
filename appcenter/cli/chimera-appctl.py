#!/usr/bin/env python3
"""Chimera II Application Center: catalog and safe install-plan generator."""
from __future__ import annotations
import argparse, json, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "apps.json"
PROVIDERS = ROOT / "providers" / "providers.json"


def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def apps():
    return load(CATALOG)["apps"]


def provider_ids():
    return {p["id"] for p in load(PROVIDERS)["providers"]}


def cmd_list(args):
    for app in apps():
        print(f'{app["id"]}\t{app["name"]}\t{app["category"]}\t{app["install"]}')


def cmd_search(args):
    q = args.query.lower()
    for app in apps():
        hay = " ".join(str(app.get(k, "")) for k in ("id", "name", "category", "license")).lower()
        if q in hay:
            print(json.dumps(app, ensure_ascii=False))


def cmd_sources(args):
    for p in load(PROVIDERS)["providers"]:
        print(f'{p["id"]}\t{p["mode"]}\t{",".join(p["formats"])}')


def cmd_show(args):
    for app in apps():
        if app["id"] == args.id:
            print(json.dumps(app, indent=2, ensure_ascii=False))
            return 0
    raise SystemExit(f"unknown application: {args.id}")


def cmd_plan(args):
    for app in apps():
        if app["id"] == args.id:
            provider = app["provider"]
            if provider not in provider_ids() and provider not in {"windows-linux", "external"}:
                raise SystemExit(f"provider not registered: {provider}")
            source = app.get("homepage")
            if source and urllib.parse.urlparse(source).scheme not in {"http", "https"}:
                raise SystemExit("source must use HTTPS/HTTP")
            plan = {"application": app["id"], "provider": provider, "install": app["install"],
                    "source": source, "execute": False,
                    "note": "Review and authorize this plan before installation."}
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            return 0
    raise SystemExit(f"unknown application: {args.id}")


def build_parser():
    p = argparse.ArgumentParser(prog="chimera-appctl")
    s = p.add_subparsers(dest="command", required=True)
    s.add_parser("list").set_defaults(func=cmd_list)
    q = s.add_parser("search"); q.add_argument("query"); q.set_defaults(func=cmd_search)
    s.add_parser("sources").set_defaults(func=cmd_sources)
    q = s.add_parser("show"); q.add_argument("id"); q.set_defaults(func=cmd_show)
    q = s.add_parser("install-plan"); q.add_argument("id"); q.set_defaults(func=cmd_plan)
    return p


if __name__ == "__main__":
    raise SystemExit(build_parser().parse_args().func(build_parser().parse_args()))
