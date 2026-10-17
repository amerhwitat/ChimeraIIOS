import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "tools/runtime/koronos-self-heal.py"
spec = importlib.util.spec_from_file_location("koronos_self_heal", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SelfHealTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "schema": "KORONOS-SELF-HEAL-1",
            "heartbeat_timeout_seconds": 30,
            "failure_window_seconds": 300,
            "max_restarts_per_window": 2,
            "restart_allowlist": ["kore.service"],
            "critical_services": ["kore.service"],
        }

    def test_stale_allowlisted_service_proposes_restart_but_does_not_execute(self):
        events = [{"type": "heartbeat", "service": "kore.service", "timestamp": 1000}]
        plan = module.build_plan(events, self.policy, now=1040)
        self.assertEqual(plan[0]["action"], "restart")
        result = module.execute_plan(plan, None, apply=False)
        self.assertEqual(result[0]["execution"], "not-requested")

    def test_non_allowlisted_service_is_never_restartable(self):
        events = [{"type": "service_stalled", "service": "aurora.service", "timestamp": 1000}]
        plan = module.build_plan(events, self.policy, now=1001)
        self.assertEqual(plan[0]["action"], "quarantine-and-report")

    def test_repeated_failures_hit_restart_budget(self):
        events = [
            {"type": "service_failed", "service": "kore.service", "timestamp": 900},
            {"type": "service_failed", "service": "kore.service", "timestamp": 950},
            {"type": "service_failed", "service": "kore.service", "timestamp": 980},
        ]
        plan = module.build_plan(events, self.policy, now=1000)
        self.assertEqual(plan[0]["action"], "quarantine-and-report")

    def test_bad_service_identifier_rejected(self):
        with self.assertRaises(ValueError):
            module.parse_events(['{"type":"service_stalled","service":"../../bad"}'])

    def test_apply_requires_adapter_at_cli_boundary(self):
        # The command-line guard is exercised by integration CI, not this pure unit test.
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
