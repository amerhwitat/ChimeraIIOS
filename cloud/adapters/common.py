from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
import subprocess
from typing import Sequence

@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

def command_path(name: str) -> str | None:
    return shutil.which(name)

def run_argv(argv: Sequence[str], timeout: int = 120) -> CommandResult:
    p = subprocess.run(list(argv), text=True, capture_output=True, timeout=timeout, check=False)
    return CommandResult(p.returncode, p.stdout, p.stderr)

def read_plan(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "CHIMERA-PLAN-1":
        raise ValueError("unsupported Chimera plan schema")
    if data.get("execution") != "explicit-apply":
        raise ValueError("plan is not marked explicit-apply")
    if data.get("credentials") != "external":
        raise ValueError("plan must keep credentials external")
    return data

def make_plan(provider: str, source: str) -> dict:
    return {
        "schema": "CHIMERA-PLAN-1",
        "provider": provider,
        "source": str(source),
        "actions": ["validate", "provision", "configure", "verify"],
        "execution": "explicit-apply",
        "credentials": "external",
    }
