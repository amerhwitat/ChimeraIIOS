from pathlib import Path
import importlib.util

P=Path(__file__).parent/"service_orchestrator.py"
spec=importlib.util.spec_from_file_location("kore",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_topological_order():
    items=[{"name":"a","after":[]},{"name":"b","after":["a"]},{"name":"c","after":["b"]}]
    assert [x["name"] for x in m.topo(items)]==["a","b","c"]
