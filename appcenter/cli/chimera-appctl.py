#!/usr/bin/env python3
"""Chimera II Application Center catalog discovery and non-executing install plans."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "apps.json"
PROVIDERS = ROOT / "providers" / "providers.json"
ALLOWED_EXTERNAL_PROVIDERS = {"windows-linux", "external", "web"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]+$")


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def apps():
    return load(CATALOG)["apps"]


def provider_ids():
    return {provider["id"] for provider in load(PROVIDERS)["providers"]}


def availability(app):
    """Legacy entries without a status are deliberately treated as unverified."""
    return app.get("availability", "catalog-only")


def validate_catalog():
    catalog = load(CATALOG)
    if not isinstance(catalog.get("apps"), list) or not catalog["apps"]:
        raise ValueError("catalog must contain a non-empty apps array")
    known_providers = provider_ids()
    seen = set()
    errors = []
    for index, app in enumerate(catalog["apps"]):
        prefix = f"apps[{index}]"
        app_id = app.get("id", "")
        if not isinstance(app_id, str) or not ID_RE.fullmatch(app_id):
            errors.append(f"{prefix}: invalid id {app_id!r}")
        elif app_id in seen:
            errors.append(f"{prefix}: duplicate id {app_id!r}")
        seen.add(app_id)
        for field in ("name", "category", "license", "provider", "install"):
            if not isinstance(app.get(field), str) or not app[field].strip():
                errors.append(f"{prefix} ({app_id}): missing/invalid {field}")
        if not isinstance(app.get("architectures"), list) or not app["architectures"]:
            errors.append(f"{prefix} ({app_id}): architectures must be a non-empty array")
        provider = app.get("provider")
        if provider and provider not in known_providers and provider not in ALLOWED_EXTERNAL_PROVIDERS:
            errors.append(f"{prefix} ({app_id}): provider {provider!r} is not registered")
        for field in ("homepage", "source"):
            url = app.get(field)
            if url:
                parsed = urllib.parse.urlparse(url)
                if parsed.scheme != "https" or not parsed.netloc:
                    errors.append(f"{prefix} ({app_id}): {field} must be an HTTPS URL")
        if availability(app) not in {"catalog-only", "source-reviewed", "imported", "build-verified", "launch-verified", "supported", "blocked"}:
            errors.append(f"{prefix} ({app_id}): invalid availability status")
    if errors:
        raise ValueError("\n".join(errors))
    return len(catalog["apps"])


def cmd_list(args):
    for app in apps():
        print(f'{app["id"]}\t{app["name"]}\t{app["category"]}\t{app["install"]}\t{availability(app)}')


def cmd_search(args):
    query = args.query.casefold()
    fields = ("id", "name", "category", "license", "provider", "homepage", "description", "tags")
    for app in apps():
        haystack = " ".join(" ".join(value) if isinstance(value, list) else str(value or "")
                            for value in (app.get(field, "") for field in fields)).casefold()
        if query in haystack:
            print(json.dumps(app, ensure_ascii=False))


def cmd_categories(args):
    grouped = {}
    for app in apps():
        grouped.setdefault(app["category"], []).append(app)
    for category in sorted(grouped, key=str.casefold):
        if args.count:
            print(f"{category}\t{len(grouped[category])}")
        else:
            print(category)


def cmd_sources(args):
    for provider in load(PROVIDERS)["providers"]:
        print(f'{provider["id"]}\t{provider["mode"]}\t{",".join(provider["formats"])}')


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
            if provider not in provider_ids() and provider not in ALLOWED_EXTERNAL_PROVIDERS:
                raise SystemExit(f"provider not registered: {provider}")
            source = app.get("homepage") or app.get("source")
            if source:
                parsed = urllib.parse.urlparse(source)
                if parsed.scheme != "https" or not parsed.netloc:
                    raise SystemExit("source must be a valid HTTPS URL")
            plan = {
                "application": app["id"],
                "name": app["name"],
                "category": app["category"],
                "provider": provider,
                "install": app["install"],
                "source": source,
                "availability": availability(app),
                "execute": False,
                "requires_authorization": True,
                "note": "This is discovery metadata, not a verified install. Review source, license, architecture, dependencies and permissions before authorizing a target-specific installer.",
            }
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            return 0
    raise SystemExit(f"unknown application: {args.id}")


def cmd_validate(args):
    try:
        count = validate_catalog()
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"catalog validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"catalog valid: {count} entries; all entries remain subject to target-specific verification")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="chimera-appctl")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list catalog entries and their verification status").set_defaults(func=cmd_list)
    query = sub.add_parser("search", help="search names, categories, providers and descriptions")
    query.add_argument("query")
    query.set_defaults(func=cmd_search)
    categories = sub.add_parser("categories", help="list application categories")
    categories.add_argument("--count", action="store_true", help="include entry counts")
    categories.set_defaults(func=cmd_categories)
    sub.add_parser("sources", help="list configured package providers").set_defaults(func=cmd_sources)
    show = sub.add_parser("show", help="show one application's metadata")
    show.add_argument("id")
    show.set_defaults(func=cmd_show)
    plan = sub.add_parser("install-plan", help="print a non-executing installation plan")
    plan.add_argument("id")
    plan.set_defaults(func=cmd_plan)
    sub.add_parser("validate", help="validate IDs, provider references, URLs and statuses").set_defaults(func=cmd_validate)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    raise SystemExit(arguments.func(arguments))
