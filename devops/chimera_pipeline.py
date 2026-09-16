from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

STAGES = ("generate", "validate", "build", "test", "vm_validate", "artifact", "iac_plan", "deploy_gate")

@dataclass(frozen=True)
class PipelinePlan:
    stages: tuple[str, ...]

    @classmethod
    def from_data(cls, data: dict) -> "PipelinePlan":
        stages = tuple(data.get("stages", ()))
        if not stages:
            raise ValueError("pipeline has no stages")
        unknown = [s for s in stages if s not in STAGES]
        if unknown:
            raise ValueError(f"unknown pipeline stages: {unknown}")
        positions = [STAGES.index(s) for s in stages]
        if positions != sorted(positions):
            raise ValueError("pipeline stages are out of order")
        return cls(stages)

    @classmethod
    def from_file(cls, path: str | Path) -> "PipelinePlan":
        return cls.from_data(json.loads(Path(path).read_text(encoding="utf-8")))

class PipelineExecutor:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace)

    def run(self, plan: PipelinePlan, allow_deploy: bool = False) -> list[dict]:
        results = []
        for stage in plan.stages:
            if stage == "deploy_gate" and not allow_deploy:
                results.append({"stage": stage, "status": "blocked", "reason": "explicit deployment approval required"})
                break
            results.append({"stage": stage, "status": "ready"})
        return results
