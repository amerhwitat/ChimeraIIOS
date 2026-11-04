import json, shutil, tempfile, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.cognition import knowledge_database as kb

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/"data/ai/hardware_systems_knowledge.json"

class KnowledgeDatabaseTests(unittest.TestCase):
    def test_packaged_database_is_valid_and_source_attributed(self):
        data=kb.read_db(DB)
        self.assertGreaterEqual(len(data["entries"]),140)
        self.assertGreaterEqual(len(data["sources"]),25)
        self.assertTrue(all(row["source_ids"] for row in data["entries"]))

    def test_append_is_atomic_versioned_and_duplicate_safe(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"knowledge.json"
            shutil.copy2(DB,dest)
            before=kb.read_db(dest)
            source=before["sources"][0]["id"]
            item={"id":"unit-test-append-entry","domain":"Testing","title":"Append test",
              "summary":"A test entry with source provenance.","tags":["test"],
              "source_ids":[source],"status":"curated-reference","verification":"unit-test"}
            inp=Path(td)/"entry.json";inp.write_text(json.dumps(item),encoding="utf-8")
            class Args: pass
            args=Args();args.database=str(dest);args.base=None;args.input=str(inp)
            self.assertEqual(kb.append(args),0)
            after=kb.read_db(dest)
            self.assertEqual(len(after["entries"]),len(before["entries"])+1)
            self.assertEqual(after["version"],"1.0.1")
            with self.assertRaises(SystemExit):kb.append(args)

    def test_rejects_unknown_source_reference(self):
        row={"id":"bad-source-entry","domain":"Test","title":"Bad","summary":"No source",
          "tags":[],"source_ids":["missing-source"],"status":"test","verification":"test"}
        with self.assertRaises(ValueError):kb.validate_entry(row,set())

if __name__=="__main__":unittest.main()
