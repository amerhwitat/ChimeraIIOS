import json
from pathlib import Path
import importlib.util

P=Path(__file__).parents[1]/"aurora_hardware_scanner.py"
spec=importlib.util.spec_from_file_location("aurora_scanner",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_plan_is_non_destructive():
    inv={"timestamp":"t","host":{"os":"test","arch":"x"},"devices":[]}
    plan=m.make_plan(inv)
    assert plan["actions"]==[]
    assert plan["policy"]["explicit_apply"] is True
    assert len(plan["inventory_sha256"])==64
