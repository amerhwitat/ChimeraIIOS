from pathlib import Path
import json

ROOT = Path(__file__).parents[2]

def test_database_build_matrix_is_registry_consistent():
    matrix = json.loads((ROOT / "database/build-matrix.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data/registry/databases.json").read_text(encoding="utf-8"))
    ids = {entry["id"] for entry in matrix["engines"]}
    registry_ids = {entry["id"] for entry in registry["engines"]}
    assert {"sqlite", "duckdb", "rocksdb", "leveldb", "mariadb", "postgresql", "firebird", "valkey", "cassandra", "couchdb"} <= ids
    assert ids <= registry_ids
    assert all(entry.get("license") and entry.get("upstream") and entry.get("status") for entry in matrix["engines"])

def test_non_osi_source_available_engines_are_not_mislabeled():
    matrix = json.loads((ROOT / "database/build-matrix.json").read_text(encoding="utf-8"))
    excluded = {entry["id"]: entry for entry in matrix["excluded_or_separately_classified"]}
    assert excluded["mongodb-community"]["license"] == "SSPL"
    assert excluded["cockroachdb"]["license"] == "BSL-1.1"
