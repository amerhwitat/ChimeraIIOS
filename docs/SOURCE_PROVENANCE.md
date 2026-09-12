# Source provenance

`opensource/sources.json` is the canonical provenance registry for external open-source projects used by the compatibility layer. The registry intentionally stores metadata instead of copying entire upstream repositories.

## Required provenance

Each entry has an upstream HTTPS location, project identifier, SPDX/license expression or explicit upstream composite-license marker, native languages, target platforms, integration mode and a `execute_on_fetch=false` security invariant.

## Current references

- systemd: LGPL-2.1-or-later by default, with file/program exceptions documented upstream.
- PipeWire: MIT for source files with documented component exceptions.
- CUPS: Apache-2.0 with its documented linking exception.
- Samba: GPL with project-specific boundary guidance.
- Windows Terminal: MIT.
- WebKit: BSD-style/LGPL composite licensing; inspect file-level notices before vendoring.

The registry is not legal advice. Before redistributing a modified upstream component, preserve all notices and verify the exact version's license files.
