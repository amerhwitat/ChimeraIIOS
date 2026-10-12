import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / 'tools' / 'validation' / 'validate_capability_status.py'
REGISTRY = ROOT / 'docs' / 'validation' / 'capability-evidence.json'


def test_capability_registry_passes_validator():
    result = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'capabilities' in result.stdout


def test_capability_registry_preserves_non_equivalence_principles():
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    assert 'documented-is-not-implemented' in data['principles']
    assert 'cataloged-is-not-executable' in data['principles']
    assert 'compiled-is-not-booted' in data['principles']
    assert 'booted-is-not-userspace-ready' in data['principles']
    assert 'sequential-multicpu-simulation-is-not-smp' in data['principles']


def test_real_smp_remains_unverified_until_evidence_bundle_exists():
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    smp = next(cap for cap in data['capabilities'] if cap['id'] == 'real-smp')
    assert smp['status'] == 'not-verified'
    assert not smp['evidence']
    assert 'at least two independently running CPUs' in data['promotion_rules']['real-smp']
