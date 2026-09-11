from pathlib import Path
import importlib.util

ROOT = Path(__file__).parents[2]

def load(path):
    spec = importlib.util.spec_from_file_location('db_backend', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_open_source_database_catalog_contains_core_backends():
    mod = load(ROOT / 'database' / 'catalog.py')
    names = {x['name'] for x in mod.DATABASES}
    assert {'MariaDB Community Server','PostgreSQL','SQLite','DuckDB','RocksDB','LevelDB','Valkey','Apache Cassandra','Apache CouchDB'} <= names
