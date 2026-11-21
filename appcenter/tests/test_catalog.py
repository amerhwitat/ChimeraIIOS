import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cli" / "chimera-appctl.py"


def test_catalog_and_providers():
    catalog = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    providers = json.loads((ROOT / "providers/providers.json").read_text(encoding="utf-8"))
    provider_ids = {provider["id"] for provider in providers["providers"]}
    assert catalog["apps"]
    ids = [app["id"] for app in catalog["apps"]]
    assert len(ids) == len(set(ids))
    for app in catalog["apps"]:
        assert app["name"]
        assert app["architectures"]
        assert app["install"]
        assert app["provider"] in provider_ids or app["provider"] in {"external", "windows-linux", "web"}


def test_no_binary_payloads_in_catalog():
    catalog = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    for app in catalog["apps"]:
        assert app.get("source", "").lower().startswith(("https://", "http://")) or "source" not in app


def run_cli(*args):
    return subprocess.run([sys.executable, str(CLI), *args], text=True, capture_output=True, check=False)


def test_cli_validate_and_category_listing():
    validation = run_cli("validate")
    assert validation.returncode == 0, validation.stderr
    categories = run_cli("categories", "--count")
    assert categories.returncode == 0
    assert "graphics" in categories.stdout
    assert "games" in categories.stdout


def test_search_finds_paint_media_and_games():
    for query, expected_id in (("pinta", "pinta"), ("media", "vlc"), ("games", "steam")):
        result = run_cli("search", query)
        assert result.returncode == 0
        assert expected_id in result.stdout


def test_install_plan_is_explicitly_non_executing():
    result = run_cli("install-plan", "pinta")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["execute"] is False
    assert plan["requires_authorization"] is True
    assert plan["availability"] == "catalog-only"

def test_runtime_support_manifest_matches_catalog_and_stays_fail_closed():
    catalog = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "runtime-support-manifest.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in manifest["apps"]] == [item["id"] for item in catalog["apps"]]
    assert all(item["native_package"]["available"] is False for item in manifest["apps"])
    assert all(item["tests"]["native_launch"] == "not-run" for item in manifest["apps"])
    assert all(item["lifecycle"]["install"] == "not-implemented" for item in manifest["apps"])
    status = run_cli("runtime-status")
    assert status.returncode == 0
    assert "browser-prototype" in status.stdout
    assert "not-run" in status.stdout
