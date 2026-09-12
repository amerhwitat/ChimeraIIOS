# Open-source integration

Chimera II OS uses upstream open-source projects as compatibility references, adapters, fetched sources or explicitly licensed vendored components. It does not copy proprietary Windows/macOS binaries or pretend that Linux, Windows and macOS ABIs are interchangeable.

The source-of-truth registry is `opensource/sources.json`. Every record identifies upstream, SPDX/licensing information, languages, platforms, integration mode and security policy. `tools/validate_provenance.py` rejects non-HTTPS sources, duplicate IDs and any source marked for execution during acquisition.

## Service layer

`services/service_registry.json` maps common capabilities to platform backends: systemd/SCM/launchd lifecycle, D-Bus/RPC IPC, NetworkManager/native networking, PipeWire/ALSA/WASAPI/CoreAudio, CUPS/IPP/Spooler printing, udev/Plug-and-Play/IOKit discovery, Samba/SMB, timers and structured logging.

## Application layer

`applications/catalog.json` catalogs free/open-source application families. A catalog entry is metadata and a compatibility boundary; it is not an instruction to execute downloaded code. Launching an application remains an explicit, policy-controlled runtime operation.

## Acquisition

`build/open_source/fetch_sources.py` is staging-only. It requires HTTPS and an allowlisted host, limits artifact size, and optionally verifies SHA-256. It never invokes the downloaded artifact.

## Licensing

Upstream licenses remain authoritative. Composite projects such as WebKit, Qt, KDE and PipeWire can contain files/components with different licenses; file-level SPDX notices must be inspected before vendoring any subset. Compatibility wrappers written by Chimera II OS are separately attributed and licensed according to the repository policy.
