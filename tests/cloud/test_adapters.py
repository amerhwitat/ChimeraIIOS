from pathlib import Path
import json
import pytest
from cloud.adapters.kubernetes import KubernetesAdapter
from cloud.adapters.openshift import OpenShiftAdapter
from cloud.adapters.public_cloud import AwsAdapter, AzureAdapter, GcpAdapter


def test_kubernetes_plan_is_non_mutating(tmp_path: Path):
    manifest = tmp_path / "m.yaml"
    manifest.write_text("apiVersion: v1\nkind: ConfigMap\n", encoding="utf-8")
    plan = KubernetesAdapter().plan(manifest)
    assert plan["execution"] == "explicit-apply"
    assert plan["credentials"] == "external"


def test_openshift_plan_is_non_mutating(tmp_path: Path):
    manifest = tmp_path / "m.yaml"
    manifest.write_text("apiVersion: v1\nkind: ConfigMap\n", encoding="utf-8")
    plan = OpenShiftAdapter().plan(manifest)
    assert plan["provider"] == "openshift"


@pytest.mark.parametrize("adapter", [AwsAdapter(), AzureAdapter(), GcpAdapter()])
def test_public_cloud_apply_never_embeds_credentials(tmp_path: Path, adapter):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(adapter.plan("infra")), encoding="utf-8")
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    assert data["credentials"] == "external"
    with pytest.raises(PermissionError):
        adapter.apply(plan_path)
