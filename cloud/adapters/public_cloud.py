from __future__ import annotations
from pathlib import Path
import json
from .common import command_path, make_plan, read_plan

class PublicCloudAdapter:
    def __init__(self, provider: str, command: str):
        self.provider = provider
        self.command = command

    def doctor(self) -> dict:
        path = command_path(self.command)
        return {"provider": self.provider, "command": self.command, "installed": path is not None, "path": path}

    def plan(self, source: str | Path, output: str | Path | None = None) -> dict:
        data = make_plan(self.provider, source)
        if output:
            Path(output).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return data

    def apply(self, plan_path: str | Path) -> int:
        plan = read_plan(plan_path)
        if plan.get("provider") != self.provider:
            raise ValueError("plan/provider mismatch")
        raise PermissionError("provider mutation requires an explicit protected integration workflow")

class AwsAdapter(PublicCloudAdapter):
    def __init__(self): super().__init__("aws", "aws")
class AzureAdapter(PublicCloudAdapter):
    def __init__(self): super().__init__("azure", "az")
class GcpAdapter(PublicCloudAdapter):
    def __init__(self): super().__init__("gcp", "gcloud")
