import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_open_source_registry_and_schema_exist():
    assert (ROOT / "opensource" / "sources.json").is_file()
    assert (ROOT / "opensource" / "sources.schema.json").is_file()


def test_service_registry_and_schema_exist():
    assert (ROOT / "services" / "service_registry.json").is_file()
    assert (ROOT / "services" / "service_schema.json").is_file()


def test_application_catalog_and_schema_exist():
    assert (ROOT / "applications" / "catalog.json").is_file()
    assert (ROOT / "applications" / "application_schema.json").is_file()


def test_registry_entries_have_provenance_fields():
    data = json.loads((ROOT / "opensource" / "sources.json").read_text(encoding="utf-8"))
    assert data["schema"] == "CHM-OSS-SOURCES-1"
    assert data["sources"]
    for item in data["sources"]:
        assert item["id"]
        assert item["upstream"]
        assert item["spdx"]
        assert item["languages"]
        assert item["platforms"]
