import importlib.util, tempfile, unittest
from pathlib import Path
MODULE=Path(__file__).resolve().parents[1]/"tools"/"userspace"/"taskmon.py"
spec=importlib.util.spec_from_file_location("taskmon",MODULE)
taskmon=importlib.util.module_from_spec(spec); spec.loader.exec_module(taskmon)
class TaskMonTests(unittest.TestCase):
    def test_empty_proc_root_has_defined_metrics(self):
        with tempfile.TemporaryDirectory() as tmp: result=taskmon.linux_snapshot(Path(tmp))
        self.assertEqual(result["process_count"],0); self.assertEqual(result["memory"]["total_bytes"],0)
        self.assertIsNone(result["memory"]["used_percent"])
    def test_render_handles_empty_process_table(self):
        result={"platform":"test","process_count":0,"processes":[],"memory":{"total_bytes":0,"available_bytes":0,"used_bytes":0,"used_percent":None,"swap_total_bytes":0,"swap_used_bytes":0,"swap_used_percent":0.0},"telemetry":{"note":"test"}}
        rendered=taskmon.render(result,"memory",10)
        self.assertIn("TaskMon",rendered); self.assertIn("processes: 0",rendered); self.assertIn("RSS",rendered)
    def test_bytes_formatting(self):
        self.assertEqual(taskmon._fmt_bytes(None),"n/a"); self.assertEqual(taskmon._fmt_bytes(1024),"1.0KiB")
if __name__=="__main__": unittest.main()
