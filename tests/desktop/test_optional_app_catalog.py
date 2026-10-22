import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "desktop" / "aurora" / "repository_application_center.py"
SPEC = importlib.util.spec_from_file_location("aurora_repository_application_center", MODULE)
CENTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CENTER)


def test_optional_catalog_is_loaded_as_discovery_only(tmp_path):
    app_catalog = tmp_path / "apps.json"
    repository_catalog = tmp_path / "repos.json"
    optional_catalog = tmp_path / "optional.json"
    app_catalog.write_text(json.dumps({"apps": []}), encoding="utf-8")
    repository_catalog.write_text(json.dumps({"source_repositories": []}), encoding="utf-8")
    optional_catalog.write_text(json.dumps({"apps": [{
        "id": "sample-editor", "name": "Sample Editor", "category": "creative",
        "license": "MIT", "upstream": "https://example.org/editor",
        "platforms": ["Windows", "Linux"], "default_installed": False
    }]}), encoding="utf-8")

    entries = CENTER.load_entries(app_catalog, repository_catalog, optional_catalog)
    item = next(entry for entry in entries if entry["id"] == "sample-editor")
    assert item["kind"] == "Optional application"
    assert item["status"] == "catalog-only · Windows, Linux"
    assert item["url"] == "https://example.org/editor"
    assert "not verified" in item["description"]
    assert "platforms" in item


def test_missing_optional_catalog_fails_closed(tmp_path):
    app_catalog = tmp_path / "apps.json"
    repository_catalog = tmp_path / "repos.json"
    app_catalog.write_text(json.dumps({"apps": []}), encoding="utf-8")
    repository_catalog.write_text(json.dumps({"source_repositories": []}), encoding="utf-8")
    entries = CENTER.load_entries(app_catalog, repository_catalog, tmp_path / "missing.json")
    assert any(entry["id"] == "optional-catalog-status" and entry["status"] == "unavailable" for entry in entries)
