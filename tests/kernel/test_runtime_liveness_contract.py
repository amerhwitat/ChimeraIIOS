from pathlib import Path
import unittest


class KoronosRuntimeLivenessContract(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.runtime = (self.root / "kernel/core/runtime_loop.cpp").read_text()
        self.koronos = (self.root / "kernel/core/koronos.cpp").read_text()

    def test_monitor_has_a_registered_idle_wake_target(self):
        self.assertIn('extern "C" {\\nuint32_t koronos_monitor_task_id = 0;\\n}', self.koronos)
        self.assertIn('if (m > 0) koronos_monitor_task_id = (uint32_t)m;', self.koronos)

    def test_monitor_blocks_after_each_snapshot(self):
        monitor = self.koronos.split("static void task_monitor(void *)", 1)[1]
        monitor = monitor.split("static void task_kore", 1)[0]
        self.assertIn("chimera_sched_block();", monitor)
        self.assertNotIn("if (++ticks > 1u)", monitor)

    def test_idle_loop_reawakens_monitor_only_when_idle(self):
        self.assertIn("if(dispatched==0 && koronos_monitor_task_id!=0", self.runtime)
        self.assertIn("chimera_sched_wake(koronos_monitor_task_id);", self.runtime)
        self.assertIn("(spin&0x00FFFFFFu)==0", self.runtime)

    def test_heartbeat_counts_total_dispatches_not_only_last_idle_iteration(self):
        self.assertIn("total_dispatched+=dispatched;", self.runtime)
        self.assertIn("vga_heartbeat(spin,total_dispatched,", self.runtime)


if __name__ == "__main__":
    unittest.main()
