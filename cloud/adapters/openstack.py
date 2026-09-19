from __future__ import annotations
from pathlib import Path
import json
from .common import command_path, make_plan, read_plan, run_argv

class OpenStackAdapter:
    provider = "openstack"
    command = "openstack"

    def doctor(self) -> dict:
        return {"provider": self.provider, "command": self.command, "installed": command_path(self.command) is not None}

    def validate_context(self) -> dict:
        if not command_path(self.command):
            return {"ok": False, "error": "openstack client not installed"}
        r = run_argv([self.command, "token", "issue", "-f", "json"])
        return {"ok": r.returncode == 0, "error": r.stderr.strip()}

    def plan(self, terraform_dir: str | Path, output: str | Path | None = None) -> dict:
        data = make_plan(self.provider, terraform_dir)
        if output:
            Path(output).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return data

    def apply(self, plan_path: str | Path) -> int:
        plan = read_plan(plan_path)
        if plan.get("provider") != self.provider:
            raise ValueError("plan/provider mismatch")
        raise PermissionError("OpenStack mutation requires the protected Terraform deployment workflow")
