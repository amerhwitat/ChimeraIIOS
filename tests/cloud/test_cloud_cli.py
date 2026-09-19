import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "cloud" / "chimera_cloud.py"


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_provider_registry():
    result = run("providers")
    assert result.returncode == 0
    for name in ("kubernetes", "openshift", "openstack", "aws", "azure", "gcp"):
        assert name in result.stdout


def test_plan_is_non_mutating(tmp_path):
    output = tmp_path / "plan.json"
    result = run("plan", "openstack", "--output", str(output))
    assert result.returncode == 0
    data = json.loads(output.read_text())
    assert data["provider"] == "openstack"
    assert data["execution"] == "explicit-apply"


def test_apply_requires_explicit_external_runner(tmp_path):
    output = tmp_path / "plan.json"
    run("plan", "kubernetes", "--output", str(output))
    result = run("apply", "--provider", "kubernetes", "--plan", str(output))
    assert result.returncode != 0
    assert "Refusing implicit infrastructure mutation" in result.stdout
