import hashlib
from pathlib import Path

import pytest

from drivers.python.driver_acquisition import (
    AcquisitionPolicy,
    DriverArtifact,
    HardwareId,
    discover_sources,
    match_hardware,
    verify_sha256,
)


def test_checksum_accepts_exact_sha256(tmp_path: Path):
    artifact = tmp_path / "driver.bin"
    artifact.write_bytes(b"chimera-driver")
    digest = hashlib.sha256(b"chimera-driver").hexdigest()
    assert verify_sha256(artifact, digest)


def test_checksum_rejects_wrong_sha256(tmp_path: Path):
    artifact = tmp_path / "driver.bin"
    artifact.write_bytes(b"chimera-driver")
    assert not verify_sha256(artifact, "0" * 64)


def test_hardware_id_matches_vendor_device():
    candidate = HardwareId(bus="pci", vendor="8086", device="1234")
    assert match_hardware(candidate, (candidate,))


def test_hardware_id_mismatch_is_rejected():
    candidate = HardwareId(bus="pci", vendor="8086", device="1234")
    other = HardwareId(bus="pci", vendor="10de", device="1234")
    assert not match_hardware(candidate, (other,))


def test_strict_policy_rejects_untrusted_windows_artifact():
    artifact = DriverArtifact(
        name="example",
        platform="windows",
        package_type="inf",
        url="https://vendor.example/driver.inf",
        sha256="0" * 64,
        hardware_ids=(HardwareId("pci", "8086", "1234"),),
        signed=False,
    )
    with pytest.raises(ValueError):
        AcquisitionPolicy().validate(artifact)


def test_linux_kernel_module_requires_abi_match():
    artifact = DriverArtifact(
        name="example",
        platform="linux",
        package_type="kernel-module",
        url="https://kernel.example/example.ko",
        sha256="0" * 64,
        hardware_ids=(HardwareId("pci", "8086", "1234"),),
        signed=True,
        kernel_abi="6.12-chimera",
    )
    with pytest.raises(ValueError):
        AcquisitionPolicy(kernel_abi="6.11-chimera").validate(artifact)


def test_discover_sources_finds_linux_kernel():
    results = discover_sources("linux", "kernel")
    assert results
    assert all(item["url"].startswith("https://") for item in results)


# The official-source importer is deliberately loaded without running main().
import importlib.util
from subprocess import CompletedProcess

_OFFICIAL_SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "acquire_official_driver_sources.py"
)
_OFFICIAL_SOURCE_SPEC = importlib.util.spec_from_file_location(
    "chimera_official_driver_sources", _OFFICIAL_SOURCE_PATH
)
assert _OFFICIAL_SOURCE_SPEC is not None and _OFFICIAL_SOURCE_SPEC.loader is not None
_OFFICIAL_DRIVER_SOURCES = importlib.util.module_from_spec(_OFFICIAL_SOURCE_SPEC)
_OFFICIAL_SOURCE_SPEC.loader.exec_module(_OFFICIAL_DRIVER_SOURCES)


def test_failed_external_clone_is_not_reported_as_acquired(tmp_path: Path, monkeypatch):
    def failed_clone(args):
        destination = Path(args[-1])
        (destination / ".git").mkdir(parents=True, exist_ok=True)
        return CompletedProcess(
            args,
            128,
            "",
            "error: failed to encode netvadapter.inf from UTF-8 to UTF-16LE-BOM",
        )

    monkeypatch.setattr(_OFFICIAL_DRIVER_SOURCES, "run_git", failed_clone)
    row = _OFFICIAL_DRIVER_SOURCES.acquire_source(
        "windows-driver-samples",
        "https://github.com/microsoft/Windows-driver-samples.git",
        tmp_path,
    )

    assert row["status"] == "checkout_failed"
    assert row["working_tree_present"] is True
    assert _OFFICIAL_DRIVER_SOURCES.summarize([row]) == {
        "acquired": 0,
        "failed": 1,
        "reference_only": 0,
    }


def test_successful_external_clone_records_revision(tmp_path: Path, monkeypatch):
    def successful_git(args):
        if args[1] == "clone":
            destination = Path(args[-1])
            (destination / ".git").mkdir(parents=True, exist_ok=True)
            return CompletedProcess(args, 0, "", "")
        return CompletedProcess(args, 0, "a" * 40 + "\\n", "")

    monkeypatch.setattr(_OFFICIAL_DRIVER_SOURCES, "run_git", successful_git)
    row = _OFFICIAL_DRIVER_SOURCES.acquire_source(
        "linux", "https://github.com/torvalds/linux.git", tmp_path
    )

    assert row["status"] == "checked_out"
    assert row["revision"] == "a" * 40
    assert _OFFICIAL_DRIVER_SOURCES.summarize([row]) == {
        "acquired": 1,
        "failed": 0,
        "reference_only": 0,
    }


def test_reference_only_apis_are_not_counted_as_acquired():
    assert _OFFICIAL_DRIVER_SOURCES.summarize(
        [{"name": "apple-driverkit", "status": "reference_only"}]
    ) == {
        "acquired": 0,
        "failed": 0,
        "reference_only": 1,
    }
