# Apache ecosystem for Chimera II OS

Chimera II OS integrates the Apache Software Foundation (ASF) ecosystem through a release-aware package ingestion layer rather than copying the entire ASF distribution into the Git repository or every ISO.

## Architecture

1. Project catalog — generated ASF project metadata is refreshed from the official Apache Projects Directory.
2. Release resolver — resolves a project against the official downloads.apache.org release tree.
3. Artifact verification — rejects snapshots, nightlies, /dev artifacts, release candidates and unapproved builds.
4. Cryptographic verification — downloads and verifies the detached OpenPGP signature and checks published SHA-512/SHA-256 digests when available.
5. License verification — requires LICENSE and NOTICE in the released payload.
6. Provenance — records artifact URL, digest, signature status and license/notice locations.
7. Koronos boundary — Apache software remains userland services, libraries and applications; it is never linked into the Koronos kernel.

The ASF release policy requires official releases to contain signed source packages and permits matching convenience binaries. Chimera therefore prefers official source releases and only accepts official release artifacts.

## Commands

Refresh the complete project catalog:

    apache-sync.py catalog

Resolve the newest release directory exposed by the ASF distribution tree:

    apache-sync.py resolve airflow

Install an explicitly resolved official release:

    apache-sync.py install airflow 3.x.y https://downloads.apache.org/airflow/.../artifact.tar.gz

The installer verifies the detached .asc signature and published checksum before unpacking the release.

## ISO integration

build-chimera-iso.sh now stages:

- /opt/chimera/apache/
- /var/cache/chimera/apache/
- /etc/chimera/apache-ecosystem.conf
- /usr/bin/apache-sync.py
- /usr/bin/install-apache-ecosystem.sh
- /usr/bin/verify-apache-package.sh
- /usr/share/chimera/config/apache-sandbox.json

Use --skip-apache to omit the integration from an ISO build. The default is to include it.

The ISO build does not download hundreds of third-party archives into Git or blindly embed every Apache release. It embeds the package-management/control-plane implementation and refreshes the complete ASF catalog when network access and Python are available.

## Authoritative ASF sources

- Apache Projects Directory: https://projects.apache.org/
- Official release distribution: https://downloads.apache.org/
- ASF Release Policy: https://www.apache.org/legal/release-policy.html
- ASF Release Creation Process: https://infra.apache.org/release-publishing.html
- ASF Release Catalog: https://release-catalog.apache.org/

The project directory is generated from project-maintained DOAP data; the ASF distribution infrastructure is the authoritative location for official release artifacts.
