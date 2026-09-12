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
