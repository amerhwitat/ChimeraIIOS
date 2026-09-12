"""Secure driver acquisition primitives for Chimera II OS.

This module never executes or kernel-loads downloaded code. It verifies metadata,
checks hardware IDs, validates trust policy, and stages artifacts for a separate
installation subsystem.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "acquisition_sources.json"


@dataclass(frozen=True)
class HardwareId:
    bus: str
    vendor: str
    device: str
    subsystem: str | None = None


@dataclass(frozen=True)
class DriverArtifact:
    name: str
    platform: str
    package_type: str
    url: str
    sha256: str
    hardware_ids: tuple[HardwareId, ...]
    signed: bool
    kernel_abi: str | None = None
    license_spdx: str | None = None
    source_url: str | None = None


class AcquisitionPolicy:
    def __init__(
        self,
        allowed_hosts: tuple[str, ...] = (
            "kernel.org",
            "www.kernel.org",
            "github.com",
            "raw.githubusercontent.com",
            "learn.microsoft.com",
            "download.microsoft.com",
        ),
        kernel_abi: str | None = None,
        require_signature: bool = True,
        max_download_bytes: int = 512 * 1024 * 1024,
    ) -> None:
        self.allowed_hosts = allowed_hosts
        self.kernel_abi = kernel_abi
        self.require_signature = require_signature
        self.max_download_bytes = max_download_bytes

    def validate(self, artifact: DriverArtifact) -> None:
        parsed = urlparse(artifact.url)
        if parsed.scheme != "https":
            raise ValueError("driver sources must use HTTPS")
        if parsed.hostname not in self.allowed_hosts:
            raise ValueError("driver source is not allowlisted")
        if len(artifact.sha256) != 64 or any(c not in "0123456789abcdef" for c in artifact.sha256.lower()):
            raise ValueError("invalid SHA-256 metadata")
        if self.require_signature and not artifact.signed:
            raise ValueError("driver artifact is not trusted/signed")
        if artifact.platform == "linux" and artifact.package_type == "kernel-module":
            if not self.kernel_abi or artifact.kernel_abi != self.kernel_abi:
                raise ValueError("Linux kernel module ABI does not match Chimera")
        if artifact.platform == "windows" and artifact.package_type not in {"inf", "driver-package"}:
            raise ValueError("unsupported Windows driver package type")


def discover_sources(platform: str, query: str) -> list[dict]:
    """Search only the curated source catalog; no arbitrary web execution."""
    data = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    entries = data.get(platform, [])
    needle = query.casefold()
    return [entry for entry in entries if needle in entry.get("name", "").casefold() or needle in entry.get("url", "").casefold()]


def verify_sha256(path: Path, expected: str) -> bool:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower() == expected.lower()


def match_hardware(device: HardwareId, candidates: tuple[HardwareId, ...]) -> bool:
    return any(
        device.bus.lower() == item.bus.lower()
        and device.vendor.lower() == item.vendor.lower()
        and device.device.lower() == item.device.lower()
        and (item.subsystem is None or item.subsystem.lower() == (device.subsystem or "").lower())
        for item in candidates
    )


def acquire_artifact(artifact: DriverArtifact, destination: Path, policy: AcquisitionPolicy) -> Path:
    """Download one allowlisted artifact, enforcing a bounded response and digest."""
    policy.validate(artifact)
    request = Request(artifact.url, headers={"User-Agent": "ChimeraIIOS-DriverBroker/1"})
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / Path(urlparse(artifact.url).path).name
    if not target.name:
        raise ValueError("artifact URL has no filename")
    with urlopen(request, timeout=30) as response, target.open("wb") as handle:
        total = 0
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            if total > policy.max_download_bytes:
                target.unlink(missing_ok=True)
                raise ValueError("driver download exceeds configured size limit")
            handle.write(block)
    if not verify_sha256(target, artifact.sha256):
        target.unlink(missing_ok=True)
        raise ValueError("SHA-256 verification failed")
    return target


def stage_artifact(path: Path, artifact: DriverArtifact, destination: Path, policy: AcquisitionPolicy) -> Path:
    """Verify and copy an artifact into a quarantine/staging directory."""
    policy.validate(artifact)
    if not verify_sha256(path, artifact.sha256):
        raise ValueError("SHA-256 verification failed")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / path.name
    target.write_bytes(path.read_bytes())
    return target
