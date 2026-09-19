from __future__ import annotations
import json
import subprocess
from pathlib import Path

class CloudFabricClient:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def providers(self) -> list[str]:
        data = json.loads((self.root / "cloud/providers.json").read_text(encoding="utf-8"))
        return list(data["providers"])

    def plan(self, provider: str, output: str = "chimera-plan.json") -> int:
        return subprocess.run(["python3", str(self.root / "tools/cloud/chimera_cloud.py"), "plan", provider, "--output", output], check=False).returncode

    def apply(self, provider: str, plan: str) -> int:
        return subprocess.run(["python3", str(self.root / "tools/cloud/chimera_cloud.py"), "apply", "--provider", provider, "--plan", plan], check=False).returncode
