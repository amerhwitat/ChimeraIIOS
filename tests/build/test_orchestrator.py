import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'build'))
import orchestrator

def test_manifest_path_exists():
    assert orchestrator.MANIFEST.exists()

def test_doctor_tools_have_expected_shape(capsys):
    assert orchestrator.doctor() == 0
    out = capsys.readouterr().out
    assert 'platform' in out and 'tools' in out

def test_dry_run_configure_does_not_execute():
    assert orchestrator.configure(ROOT / 'build-test', dry_run=True) == 0

def test_dry_run_build_does_not_execute():
    assert orchestrator.native_build(ROOT / 'build-test', jobs=2, dry_run=True) == 0

def test_dry_run_package_does_not_execute():
    assert orchestrator.native_package(ROOT / 'build-test', dry_run=True) == 0
