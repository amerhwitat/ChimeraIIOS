from __future__ import annotations
from pathlib import Path
import json
from .common import command_path, make_plan, read_plan, run_argv

class KubernetesAdapter:
    provider = "kubernetes"
    command = "kubectl"

    def doctor(self) -> dict:
        return {"provider": self.provider, "command": self.command, "installed": command_path(self.command) is not None}

    def validate_context(self) -> dict:
        if not command_path(self.command):
            return {"ok": False, "error": "kubectl not installed"}
        r = run_argv([self.command, "config", "current-context"])
        return {"ok": r.returncode == 0, "context": r.stdout.strip(), "error": r.stderr.strip()}

    def plan(self, manifest_path: str | Path, output: str | Path | None = None) -> dict:
        manifest = Path(manifest_path)
        if not manifest.is_file():
            raise FileNotFoundError(manifest)
        data = make_plan(self.provider, manifest)
        if output:
            Path(output).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return data

    def apply(self, plan_path: str | Path) -> int:
        plan = read_plan(plan_path)
        if plan.get("provider") != self.provider:
            raise ValueError("plan/provider mismatch")
        manifest = plan.get("source")
        if not manifest or not Path(manifest).is_file():
            raise FileNotFoundError(manifest or "manifest")
        return run_argv([self.command, "apply", "--filename", manifest]).returncode
