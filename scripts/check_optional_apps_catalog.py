#!/usr/bin/env python3
"""Validate the cross-platform optional-app catalog before publication.

This checks metadata and safety invariants only; it does not claim that an app
is installed, compatible, licensed for redistribution, or launchable.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "desktop" / "optional_apps_catalog.json"
ALLOWED_PLATFORMS = {"Windows", "Linux", "macOS", "Web"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_TOP_LEVEL = {"$schema", "title", "purpose", "updated", "platforms", "integration_contract", "apps"}
REQUIRED_APP_FIELDS = {"id", "name", "category", "license", "upstream", "platforms",
                       "integration", "default_installed", "launchability", "panel"}


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["catalog root must be a JSON object"]

    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        errors.append("missing top-level fields: " + ", ".join(sorted(missing)))

    if not isinstance(data.get("updated"), str):
        errors.append("updated must be an ISO date string")
    else:
        try:
            date.fromisoformat(data["updated"])
        except ValueError:
            errors.append(f"updated is not a valid ISO date: {data['updated']!r}")

    platforms = data.get("platforms")
    if not isinstance(platforms, list) or not platforms:
        errors.append("platforms must be a non-empty array")
    elif (any(not isinstance(p, str) for p in platforms)
          or len(platforms) != len(set(platforms))
          or not set(platforms) <= ALLOWED_PLATFORMS):
        errors.append("platforms contains duplicates or unsupported platform names")

    contract = data.get("integration_contract")
    if not isinstance(contract, dict):
        errors.append("integration_contract must be an object")
    else:
        for key in ("never_assume_installed", "license_review_required"):
            if contract.get(key) is not True:
                errors.append(f"integration_contract.{key} must be true")

    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        errors.append("apps must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    categories: Counter[str] = Counter()
    for index, app in enumerate(apps):
        prefix = f"apps[{index}]"
        if not isinstance(app, dict):
            errors.append(f"{prefix} must be an object")
            continue
        absent = REQUIRED_APP_FIELDS - app.keys()
        if absent:
            errors.append(f"{prefix} missing fields: " + ", ".join(sorted(absent)))
        app_id = app.get("id")
        if not isinstance(app_id, str) or not ID_PATTERN.fullmatch(app_id):
            errors.append(f"{prefix}.id must be a lowercase kebab-case identifier")
        elif app_id in seen_ids:
            errors.append(f"{prefix}.id duplicates {app_id!r}")
        else:
            seen_ids.add(app_id)

        for field in ("name", "category", "license", "panel"):
            if not isinstance(app.get(field), str) or not app[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if isinstance(app.get("category"), str):
            categories[app["category"]] += 1

        upstream = app.get("upstream")
        if not isinstance(upstream, str):
            errors.append(f"{prefix}.upstream must be a URL")
        else:
            parsed = urlsplit(upstream)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                errors.append(f"{prefix}.upstream must be an HTTPS URL without embedded credentials")

        app_platforms = app.get("platforms")
        if not isinstance(app_platforms, list) or not app_platforms:
            errors.append(f"{prefix}.platforms must be a non-empty array")
        elif (len(app_platforms) != len(set(app_platforms))
              or not set(app_platforms) <= ALLOWED_PLATFORMS):
            errors.append(f"{prefix}.platforms contains duplicates or unsupported platform names")

        web_preview = app.get("web_preview")
        if web_preview is not None:
            preview_url = urlsplit(web_preview) if isinstance(web_preview, str) else None
            if preview_url is None or preview_url.scheme != "https" or not preview_url.netloc or preview_url.username or preview_url.password:
                errors.append(f"{prefix}.web_preview must be an HTTPS URL without embedded credentials")

        if app.get("default_installed") is not False:
            errors.append(f"{prefix}.default_installed must be false; installation requires provider evidence")
        if app.get("launchability") != "not-guaranteed":
            errors.append(f"{prefix}.launchability must remain not-guaranteed until verified")
        if app.get("integration") != "external-package-or-provider":
            errors.append(f"{prefix}.integration must identify the external provider boundary")

    return errors


def main() -> int:
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read optional-app catalog: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        print(f"FAIL: optional-app catalog has {len(errors)} validation error(s).", file=sys.stderr)
        return 1

    apps = data["apps"]
    categories = Counter(app["category"] for app in apps)
    print(f"PASS: validated {len(apps)} optional apps across {len(categories)} categories.")
    print("Counts by category: " + ", ".join(f"{key}={value}" for key, value in sorted(categories.items())))
    print("Safety policy: no default installs; launchability is not assumed; upstream URLs use HTTPS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
