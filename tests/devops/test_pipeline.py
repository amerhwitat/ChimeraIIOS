import json
import pytest
from pathlib import Path
from devops.chimera_pipeline import PipelinePlan, PipelineExecutor


def test_pipeline_accepts_required_order():
    plan = PipelinePlan.from_data({"stages": ["generate", "validate", "build", "test", "vm_validate", "artifact", "iac_plan", "deploy_gate"]})
    assert plan.stages[-1] == "deploy_gate"


def test_pipeline_rejects_deploy_before_plan():
    with pytest.raises(ValueError):
        PipelinePlan.from_data({"stages": ["generate", "deploy_gate", "iac_plan"]})


def test_executor_requires_explicit_deploy_gate(tmp_path: Path):
    plan = PipelinePlan.from_data({"stages": ["validate", "iac_plan", "deploy_gate"]})
    executor = PipelineExecutor(tmp_path)
    result = executor.run(plan, allow_deploy=False)
    assert result[-1]["status"] == "blocked"
