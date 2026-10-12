# Aurora architecture, ISA and desktop-profile discovery

Aurora can periodically run `tools/architecture_discovery/chimera_discovery.py` to produce an auditable candidate report for new CPU families, ISA extensions and compatibility-backend work. The scheduled GitHub Actions workflow runs weekly; online checks are opt-in on manual dispatch. A local or packaged runtime may call the same CLI from a supervised timer/service, but the Aurora UI must show last scan time, source errors, candidate status and review state instead of silently advertising support.

## Data flow

1. Read the canonical ISA inventory (currently checked in from `isa/isa_database.json` or `data/isa/isa_database.json`, if present).
2. Optionally fetch only configured HTTPS text sources on an explicit host allowlist, with per-source timeout and response-size limits.
3. Record source URL, content hash, matched architecture/ISA terms, scan timestamp and fetch errors.
4. Emit candidates and compatibility-backend proposals as `candidate-only` / `proposal-only`.
5. Require human review of the normative specification, encoding, operand constraints, semantics, exceptions, ABI and licensing before modifying executable instruction rows.
6. Build and test an implementation in isolated CI. Promote status only with evidence from decoder/encoder tests, execution tests, normative conformance suites and target-specific build/boot evidence.

The scanner is metadata discovery, not an RNN/LLM training pipeline. A future RNN/LLM component may rank and explain candidates, but must not autonomously generate privileged code, mark compatibility complete, or install drivers. Keep model outputs advisory and store provenance plus a human approval record.

## Builder and runtime integration

The canonical build remains `./build-chimera-iso.sh`. Discovery is a separate bounded stage/artifact so transient network failure does not corrupt the ISA database or make offline builds nondeterministic. The workflow artifact can be reviewed and then imported through the normal reviewed registry update. Do not make a full ISO build depend on arbitrary internet crawling.

For runtime integration, expose the report through an Aurora “Architecture & Compatibility Research” panel and run the scanner from a supervised service/timer with configurable interval, offline mode, cancellation, logs, and resource limits. Do not start network work on the compositor/render thread. No runtime timer/service is claimed to be installed by this research tool alone.

## Linux distribution and desktop environments

`config/compatibility/distro-desktop-profiles.json` is a selectable integration catalog, not a claim that all distributions are imported or currently bootable. The practical path is to import a pinned, verified OCI root filesystem into an isolated profile, inventory packages and licenses, adapt session startup, display/audio/input, D-Bus and portals, map filesystem and service expectations, and test each desktop/session on each supported host/runtime.

Candidate profiles include Debian/GNOME, Ubuntu/GNOME, Fedora/GNOME, openSUSE/Plasma, Arch/Plasma and Linux Mint/Cinnamon, plus XFCE, LXQt, MATE and COSMIC session targets. Image availability, signatures, redistribution rights, hardware acceleration and runtime compatibility must be checked before a profile becomes supported. Do not merge foreign Linux kernels into Koronos; retain Koronos as the native kernel and run imported userlands behind explicit compatibility/container boundaries.

## Status semantics

- **Discovered**: a configured source contained a matching term.
- **Cataloged**: reviewed metadata exists in the canonical registry.
- **Implemented**: code exists and focused tests exercise it.
- **Compiled**: a named artifact was produced for a named target.
- **Booted/userspace-ready**: runtime evidence demonstrates the relevant milestone.
- **Conformance-tested**: normative tests pass for the declared scope.

None of these statuses should be inferred from a model recommendation, a source URL, a rootfs download, or a successful metadata scan.
