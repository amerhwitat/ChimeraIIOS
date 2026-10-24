import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "userspace" / "taskmon.py"
spec = importlib.util.spec_from_file_location("taskmon", MODULE)
taskmon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taskmon)


class TaskMonTests(unittest.TestCase):
    def test_empty_proc_root_has_defined_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = taskmon.linux_snapshot(Path(tmp))
        self.assertEqual(result["process_count"], 0)
        self.assertEqual(result["memory"]["total_bytes"], 0)
        self.assertIsNone(result["memory"]["used_percent"])

    def test_parses_realistic_procfs_memory_and_process_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "meminfo").write_text(
                "MemTotal: 1024 kB\nMemAvailable: 512 kB\n"
                "SwapTotal: 128 kB\nSwapFree: 64 kB\n",
                encoding="utf-8",
            )
            proc = root / "123"
            proc.mkdir()
            fields = ["0"] * 22
            fields[0] = "S"       # state (stat field 3)
            fields[11] = "7"      # user CPU ticks (field 14)
            fields[12] = "5"      # system CPU ticks (field 15)
            fields[20] = "8192"   # virtual bytes (field 23)
            fields[21] = "3"      # resident pages (field 24)
            # Parentheses in a process name are legal; parsing must use the final ')'.
            (proc / "stat").write_text(
                "123 (worker ) alpha) " + " ".join(fields), encoding="utf-8"
            )
            (proc / "status").write_text("Name:\tworker\nUid:\t1000\t1000\t1000\t1000\n",
                                         encoding="utf-8")
            result = taskmon.linux_snapshot(root)

        self.assertEqual(result["process_count"], 1)
        process = result["processes"][0]
        self.assertEqual(process["pid"], 123)
        self.assertEqual(process["name"], "worker ) alpha")
        self.assertEqual(process["uid"], 1000)
        self.assertEqual(process["virtual_bytes"], 8192)
        self.assertEqual(process["rss_bytes"], 3 * os.sysconf("SC_PAGE_SIZE"))
        self.assertEqual(process["cpu_ticks"], 12)
        self.assertEqual(result["memory"]["total_bytes"], 1024 * 1024)
        self.assertEqual(result["memory"]["available_bytes"], 512 * 1024)
        self.assertEqual(result["memory"]["swap_used_bytes"], 64 * 1024)

    def test_malformed_process_stat_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proc = root / "44"
            proc.mkdir()
            (proc / "stat").write_text("not a valid proc stat line", encoding="utf-8")
            result = taskmon.linux_snapshot(root)
        self.assertEqual(result["process_count"], 0)

    def test_render_handles_empty_process_table(self):
        result = {
            "platform": "test",
            "process_count": 0,
            "processes": [],
            "memory": {
                "total_bytes": 0, "available_bytes": 0, "used_bytes": 0,
                "used_percent": None, "swap_total_bytes": 0,
                "swap_used_bytes": 0, "swap_used_percent": 0.0,
            },
            "telemetry": {"note": "test"},
        }
        rendered = taskmon.render(result, "memory", 10)
        self.assertIn("TaskMon", rendered)
        self.assertIn("processes: 0", rendered)
        self.assertIn("RSS", rendered)

    def test_bytes_formatting(self):
        self.assertEqual(taskmon._fmt_bytes(None), "n/a")
        self.assertEqual(taskmon._fmt_bytes(1024), "1.0KiB")


if __name__ == "__main__":
    unittest.main()
