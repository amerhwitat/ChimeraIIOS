# Apache ecosystem for Chimera II OS

Chimera II OS now has an Apache ecosystem package-ingestion framework covering the complete ASF project catalog rather than a fixed hand-maintained shortlist.

The ASF project directory is generated from project-maintained DOAP data and refreshed regularly. Current official releases are published through ASF distribution infrastructure. ASF release policy requires official source releases and permits convenience binaries only when they correspond to the same released source version.

The Chimera installer therefore resolves the ASF catalog, selects official releases, verifies checksums/signatures and LICENSE/NOTICE metadata, then installs packages as Koronos userland services. It does not copy hundreds of projects or gigabytes of third-party artifacts into the Git repository itself.

This distinction matters: the ASF directory contains hundreds of projects, and ASF explicitly requires distribution from approved release artifacts rather than nightly/snapshot/unapproved material.
