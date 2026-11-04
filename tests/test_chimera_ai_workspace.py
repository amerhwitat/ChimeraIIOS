#!/usr/bin/env python3
"""Regression tests for the local AI Workspace index and CLI contracts."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "chimera-ai-workspace.py"

class AIWorkspaceTests(unittest.TestCase):
    def test_index_defaults_to_metadata_and_excludes_private_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "resources"
            root.mkdir()
            (root / "public.md").write_text("Public project documentation", encoding="utf-8")
            (root / ".env").write_text("TOKEN=not-for-index", encoding="utf-8")
            (root / ".hidden.md").write_text("hidden material", encoding="utf-8")
            (root / "id_rsa").write_text("private key", encoding="utf-8")
            (root / "credentials").mkdir()
            (root / "credentials" / "account.json").write_text('{"secret":"x"}', encoding="utf-8")
            (root / "secrets").mkdir()
            (root / "secrets" / "notes.md").write_text("secret notes", encoding="utf-8")
            database = Path(tmp) / "resources.json"
            subprocess.run([sys.executable, str(SCRIPT), "scan", "--root", str(root),
                            "--database", str(database)], check=True, capture_output=True, text=True)
            payload = json.loads(database.read_text(encoding="utf-8"))
            self.assertEqual(payload["resource_count"], 1)
            self.assertEqual(payload["resources"][0]["path"], "public.md")
            self.assertNotIn("text", payload["resources"][0])

    def test_text_capture_requires_explicit_opt_in_and_cli_surfaces_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "resources"
            root.mkdir()
            (root / "public.md").write_text("retrievable public context", encoding="utf-8")
            database = Path(tmp) / "resources.json"
            subprocess.run([sys.executable, str(SCRIPT), "scan", "--root", str(root),
                            "--database", str(database), "--include-text"], check=True,
                           capture_output=True, text=True)
            payload = json.loads(database.read_text(encoding="utf-8"))
            self.assertEqual(payload["resources"][0]["text"], "retrievable public context")
        for command in ("chat", "infer", "rnn-score"):
            result = subprocess.run([sys.executable, str(SCRIPT), command, "--help"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        chat_help = subprocess.run([sys.executable, str(SCRIPT), "chat", "--help"],
                                   capture_output=True, text=True, check=True).stdout
        self.assertIn("--knowledge-database", chat_help)

    def test_chat_retrieval_uses_source_attributed_hardware_knowledge(self):
        import importlib.util
        database = Path(__file__).resolve().parents[1] / "data" / "ai" / "hardware_systems_knowledge.json"
        spec = importlib.util.spec_from_file_location("chimera_ai_workspace_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        matches = module.retrieve_knowledge_context(str(database), "NVMe DMA queue", 5)
        self.assertTrue(matches)
        self.assertTrue(any(source.get("url") for source in matches[0].get("sources", [])))

if __name__ == "__main__":
    unittest.main()
