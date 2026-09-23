#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(os.environ.get("CHIMERA_APACHE_PREFIX", "/opt/chimera/apache"))
CACHE = Path(os.environ.get("CHIMERA_APACHE_CACHE", "/var/cache/chimera/apache"))
PROJECT_INDEX = os.environ.get("CHIMERA_APACHE_PROJECT_INDEX", "https://projects.apache.org/json/projects/")
RELEASE_INDEX = os.environ.get("CHIMERA_APACHE_RELEASE_INDEX", "https://downloads.apache.org/")
USER_AGENT = "Chimera-II-OS-Apache-Integrator/2.0"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError(f"invalid project/version name: {value}")
    return value


def reject_unreleased(url: str) -> None:
    lower = url.lower()
    blocked = ("snapshot", "nightly", "unapproved", "/dev/", "release-candidate", "-rc")
    if any(token in lower for token in blocked):
        raise ValueError(f"non-official or pre-release artifact rejected: {url}")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


def links(url: str) -> list[str]:
    parser = LinkParser()
    parser.feed(get(url).decode("utf-8", errors="replace"))
    return [urllib.parse.urljoin(url, link) for link in parser.links]


def refresh_project_catalog() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    index = CACHE / "projects-index.html"
    index.write_bytes(get(PROJECT_INDEX))
    project_urls = sorted(
        u for u in links(PROJECT_INDEX)
        if u.endswith(".json") and "/json/projects/" in u
    )
    catalog: dict[str, dict] = {}
    for url in project_urls:
        try:
            data = json.loads(get(url).decode("utf-8"))
        except Exception:
            continue
        pmc = str(data.get("pmc") or "").strip().lower()
        name = str(data.get("name") or "").strip()
        if pmc:
            catalog[pmc] = {
                "name": name,
                "pmc": pmc,
                "category": data.get("category"),
                "download-page": data.get("download-page"),
                "homepage": data.get("homepage"),
                "repository": data.get("repository"),
                "source": url,
            }
    output = BASE / "apache-project-catalog.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "source": PROJECT_INDEX,
                "project_count": len(catalog),
                "projects": catalog,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def resolve_release(project: str) -> dict:
    project = safe_name(project).lower()
    base = RELEASE_INDEX.rstrip("/") + "/" + urllib.parse.quote(project) + "/"
    candidates = [u for u in links(base) if u.endswith("/") and urllib.parse.urlparse(u).path.rstrip("/").split("/")[-1]]
    candidates = [u for u in candidates if re.search(r"/[0-9][^/]*/$", u)]
    if not candidates:
        raise RuntimeError(f"no official release directories found for {project}: {base}")

    def version_key(url: str):
        value = urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1]
        nums = tuple(int(x) for x in re.findall(r"\d+", value))
        return nums, value

    release_dir = sorted(candidates, key=version_key, reverse=True)[0]
    artifacts = [u for u in links(release_dir) if not u.endswith("/") and not any(
        x in urllib.parse.urlparse(u).path.lower()
        for x in (".asc", ".sha", ".md5", "checksum", "license", "notice")
    )]
    artifacts = [u for u in artifacts if not re.search(r"(?i)(snapshot|nightly|rc\b)", u)]
    if not artifacts:
        raise RuntimeError(f"no release artifact found in {release_dir}")

    source_candidates = [
        u for u in artifacts
        if re.search(r"(?i)(source|src|apache-[^/]+\.tar\.(gz|bz2|xz)|\.zip$)", u)
    ]
    artifact = sorted(source_candidates or artifacts)[0]
    version = urllib.parse.urlparse(release_dir).path.rstrip("/").split("/")[-1]
    reject_unreleased(artifact)
    return {"project": project, "version": version, "url": artifact, "release_dir": release_dir}


def verify_pgp(artifact: Path, signature: Path) -> None:
    gpg = shutil.which("gpg")
    if not gpg:
        raise RuntimeError("gpg is required to verify Apache release signatures")
    subprocess.run(
        [gpg, "--batch", "--verify", str(signature), str(artifact)],
        check=True,
    )


def verify_published_digest(artifact: Path, release_dir: str) -> dict:
    result = {"sha256": digest(artifact), "published": {}}
    for suffix, algorithm in ((".sha512", "sha512"), (".sha256", "sha256"), (".sha", "sha256")):
        url = urllib.parse.urljoin(release_dir, artifact.name + suffix)
        try:
            text = get(url).decode("utf-8", errors="replace")
        except Exception:
            continue
        match = re.search(r"\b([0-9a-fA-F]{%d})\b" % hashlib.new(algorithm).digest_size * 2, text)
        if match:
            expected = match.group(1).lower()
            actual = digest(artifact, algorithm)
            if expected != actual:
                raise ValueError(f"{algorithm} checksum mismatch for {artifact.name}")
            result["published"][algorithm] = expected
            return result
    return result


def unpack(artifact: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if tarfile.is_tarfile(artifact):
        with tarfile.open(artifact, "r:*") as archive:
            archive.extractall(destination, filter="data" if sys.version_info >= (3, 12) else None)
        return
    if zipfile.is_zipfile(artifact):
        with zipfile.ZipFile(artifact) as archive:
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                if not str(target).startswith(str(destination.resolve()) + os.sep):
                    raise ValueError("unsafe ZIP path")
            archive.extractall(destination)
        return
    raise ValueError(f"unsupported release archive format: {artifact}")


def find_required_metadata(root: Path) -> tuple[Path, Path]:
    licenses = list(root.rglob("LICENSE"))
    notices = list(root.rglob("NOTICE"))
    if not licenses or not notices:
        raise RuntimeError("Apache artifact must contain LICENSE and NOTICE")
    return licenses[0], notices[0]


def install(project: str, version: str, url: str, expected_sha256: str | None = None) -> Path:
    project = safe_name(project)
    version = safe_name(version)
    reject_unreleased(url)
    CACHE.mkdir(parents=True, exist_ok=True)
    artifact = CACHE / Path(urllib.parse.urlparse(url).path).name
    if not artifact.exists():
        artifact.write_bytes(get(url))

    actual = digest(artifact)
    if expected_sha256 and actual.lower() != expected_sha256.lower():
        raise ValueError("SHA-256 mismatch")

    release_dir = url.rsplit("/", 1)[0] + "/"
    signature = CACHE / (artifact.name + ".asc")
    if not signature.exists():
        try:
            signature.write_bytes(get(urllib.parse.urljoin(release_dir, artifact.name + ".asc")))
        except Exception as exc:
            raise RuntimeError(f"Apache release signature not available: {artifact.name}.asc") from exc
    verify_pgp(artifact, signature)
    published = verify_published_digest(artifact, release_dir)

    with tempfile.TemporaryDirectory(prefix="chimera-apache-") as tmp:
        unpack_root = Path(tmp) / "payload"
        unpack(artifact, unpack_root)
        license_path, notice_path = find_required_metadata(unpack_root)
        target = BASE / project / version
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(unpack_root, target / "payload")
        (target / "ARTIFACT").write_text(str(artifact) + "\n", encoding="utf-8")
        (target / "SIGNATURE").write_bytes(signature.read_bytes())
        (target / "SHA256").write_text(actual + "  " + artifact.name + "\n", encoding="utf-8")
        (target / "LICENSE-PATH").write_text(str(license_path.relative_to(unpack_root)) + "\n", encoding="utf-8")
        (target / "NOTICE-PATH").write_text(str(notice_path.relative_to(unpack_root)) + "\n", encoding="utf-8")
        (target / "PROVENANCE.json").write_text(
            json.dumps(
                {
                    "project": project,
                    "version": version,
                    "source_url": url,
                    "sha256": actual,
                    "published_digests": published["published"],
                    "signature_verified": True,
                    "license_present": True,
                    "notice_present": True,
                    "artifact_policy": "official-releases-only",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Chimera II OS ASF release resolver/verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("catalog", help="refresh the complete ASF project catalog")
    resolve = sub.add_parser("resolve", help="resolve the newest official release artifact")
    resolve.add_argument("project")
    install_parser = sub.add_parser("install", help="download, verify and install an official release")
    install_parser.add_argument("project")
    install_parser.add_argument("version")
    install_parser.add_argument("url")
    install_parser.add_argument("--sha256")

    args = parser.parse_args()
    if args.command == "catalog":
        print(refresh_project_catalog())
    elif args.command == "resolve":
        print(json.dumps(resolve_release(args.project), indent=2))
    else:
        install(args.project, args.version, args.url, args.sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
