#!/usr/bin/env python3
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "chimera-run"
MANIFEST = ROOT / "os-command-runtime.json"
class RuntimeRegistryTests(unittest.TestCase):
    def test_manifest_schema_and_policy(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("chimera-native", data["providers"])
        self.assertTrue(data["policy"]["do_not_download_or_execute_untrusted_binaries_automatically"])
        for provider in data["providers"].values():
            self.assertTrue(provider["commands"])
            self.assertIn("mode", provider)
    def test_list_commands(self):
        p = subprocess.run([sys.executable, str(RUNNER), "--list"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("chimera-run", p.stdout)
        self.assertIn("powershell", p.stdout)
    def test_unknown_command_is_not_found(self):
        p = subprocess.run([sys.executable, str(RUNNER), "definitely-not-a-real-chimera-command-7d9"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 127)
        self.assertIn("command not found", p.stderr)
    def test_mode_validation(self):
        p = subprocess.run([sys.executable, str(RUNNER), "--mode", "mystery", "echo"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("mode must be", p.stderr)
    def test_native_mode_rejects_foreign_executable(self):
        import os, tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"MZ" + b"\0" * 126)
            f.flush()
            os.chmod(f.name, 0o755)
            p = subprocess.run([sys.executable, str(RUNNER), "--mode", "native", f.name], text=True, capture_output=True)
            self.assertEqual(p.returncode, 126)
            self.assertIn("not native", p.stderr)
    def test_dos_mz_binary_runs_through_emulator_without_host_exec_bit(self):
        import json, os, tempfile
        with tempfile.TemporaryDirectory() as td:
            capture = Path(td) / "args.json"
            emulator = Path(td) / "dosbox-x"
            emulator.write_text("#!/usr/bin/env python3\nimport json,os,sys\nopen(os.environ['CAPTURE_ARGS'],'w').write(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            emulator.chmod(0o755)
            program = Path(td) / "GAME.EXE"
            program.write_bytes(b"MZ" + b"\\0" * 126)
            program.chmod(0o644)
            env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""), CAPTURE_ARGS=str(capture))
            p = subprocess.run([sys.executable, str(RUNNER), "--mode", "compat", str(program), "level 2"], env=env, text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            args = json.loads(capture.read_text(encoding="utf-8"))
            self.assertEqual(args[0], "-c")
            self.assertIn(str(program.parent), args[1])
            self.assertIn(" -ro", args[1])
            self.assertEqual(args[2:5], ["-c", "c:", "-c"])
            self.assertIn('"GAME.EXE" "level 2"', args[5])

    def test_powershell_command_uses_literal_arguments(self):
        import os, tempfile
        with tempfile.TemporaryDirectory() as td:
            capture = Path(td) / "args.json"
            fake = Path(td) / "pwsh"
            fake.write_text("#!/usr/bin/env python3\nimport json,os,sys\nopen(os.environ['CAPTURE_ARGS'],'w').write(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            fake.chmod(0o755)
            env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""), CAPTURE_ARGS=str(capture))
            p = subprocess.run([sys.executable, str(RUNNER), "--mode", "compat", "Get-ChildItem", "hello world", "a'b"], env=env, text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            args = json.loads(capture.read_text(encoding="utf-8"))
            self.assertEqual(args[:3], ["-NoLogo", "-NoProfile", "-NonInteractive"])
            self.assertEqual(args[-1], "& 'Get-ChildItem' 'hello world' 'a''b'")

    def test_windows_cmd_provider_rejects_metacharacters(self):
        import os, tempfile
        with tempfile.TemporaryDirectory() as td:
            capture = Path(td) / "args.json"
            fake = Path(td) / "wine"
            fake.write_text("#!/usr/bin/env python3\nimport json,os,sys\nopen(os.environ['CAPTURE_ARGS'],'w').write(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            fake.chmod(0o755)
            env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""), CAPTURE_ARGS=str(capture))
            p = subprocess.run([sys.executable, str(RUNNER), "--mode", "compat", "ipconfig", "/all&whoami"], env=env, text=True, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("metacharacters", p.stderr)
            self.assertFalse(capture.exists())
if __name__ == "__main__":
    unittest.main()
