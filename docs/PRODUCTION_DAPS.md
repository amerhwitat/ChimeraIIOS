# Production DAPS evidence bundle

The release verifier is deliberately fail-closed. It validates an immutable ISO hash,
six target/firmware traces, and separately recorded end-to-end postconditions. A build,
a candidate probe ELF, a manifest, or a kernel-authored readiness line alone cannot pass.

Run:

```sh
python3 tools/release/verify-production-daps.py --evidence build/production-daps/evidence.json
```

All paths in the JSON are relative to the directory containing `evidence.json`.
The candidate ISO must be the exact ISO booted by every trace and end-to-end test.

## Evidence schema (version 1)

```json
{
  "schema_version": 1,
  "iso": "candidate.iso",
  "iso_sha256": "<64 lowercase hex characters>",
  "traces": {
    "live/bios": {"iso_sha256": "<same hash>", "log": "traces/live-bios.log", "payload_file": "payloads/live-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"},
    "live/uefi": {"iso_sha256": "<same hash>", "log": "traces/live-uefi.log", "payload_file": "payloads/live-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"},
    "installer/bios": {"iso_sha256": "<same hash>", "log": "traces/installer-bios.log", "payload_file": "payloads/installer-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"},
    "installer/uefi": {"iso_sha256": "<same hash>", "log": "traces/installer-uefi.log", "payload_file": "payloads/installer-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"},
    "recovery/bios": {"iso_sha256": "<same hash>", "log": "traces/recovery-bios.log", "payload_file": "payloads/recovery-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"},
    "recovery/uefi": {"iso_sha256": "<same hash>", "log": "traces/recovery-uefi.log", "payload_file": "payloads/recovery-init.elf", "payload_sha256": "<SHA-256 of extracted init ELF>"}
  },
  "installer_persistence": {
    "passed": true, "iso_sha256": "<same hash>", "write_verified": true,
    "cold_reboot_verified": true, "installed_system_ready": true,
    "evidence_log": "traces/installer-persistence.log"
  },
  "recovery": {
    "passed": true, "iso_sha256": "<same hash>", "repair_action_executed": true,
    "postcondition_verified": true, "evidence_log": "traces/recovery-repair.log"
  },
  "smp": {
    "passed": true, "iso_sha256": "<same hash>", "online_ap_cpus": [0, 1],
    "overlap_observed": true, "per_cpu_trace": "traces/smp-overlap.log"
  }
}
```

The values above are a schema example, not real acceptance evidence. Replace every
placeholder with evidence from the same candidate ISO. The verifier also reads the
referenced postcondition logs and requires these exact records:

- Installer log: `INSTALL WRITE VERIFIED`, `INSTALLED DISK COLD REBOOT VERIFIED`,
  `INSTALLED SYSTEM READY`.
- Recovery log: `RECOVERY REPAIR EXECUTED`, `RECOVERY POSTCONDITION VERIFIED`.
- Per-CPU SMP trace: `SMP AP ONLINE: cpu=<id>` for at least two distinct CPUs and
  `SMP OVERLAP VERIFIED`.

Each of the six boot traces must show, in order, kernel readiness, production payload
provenance, production init execution, a nonzero CPL3-originated syscall acknowledgement,
matching same-PID userspace readiness, and ring-3 return.
To prevent the dedicated `user-init-<target>.elf` smoke probes from being mistaken for
production acceptance, each trace must also contain both records emitted by the actual
production initramfs-to-process path:

- `PRODUCTION INIT PAYLOAD: target=<target> source=initramfs sha256=<64 lowercase hex>`
- `PRODUCTION INIT EXECUTED: target=<target> pid=<same nonzero PID>`

The production-executed PID must match both the CPL3 syscall acknowledgement and the
userspace readiness PID. Each trace record must also name the extracted production init ELF
under `payload_file` and its lowercase SHA-256 under `payload_sha256`. The verifier hashes
that file and requires the digest emitted by the kernel to match it. The payload file must be
independently extracted from the exact ISO named by the manifest; a hand-authored manifest
entry or probe-only trace is not sufficient evidence. Until the
kernel implements and emits these records from the real production payload path, DAPS
must remain blocked. Both Live firmware traces must additionally show
`USERSPACE TARGET READY: live component=aurora-session` and `AURORA READY`.

Each of the six traces must also include structured file-syscall evidence from the
same acknowledged PID, after its first CPL3 return and before readiness:

- `USERSPACE FILE SYSCALL: target=<target> pid=<pid> op=open path=/etc/os-release result=fd:<fd>`
- `USERSPACE FILE SYSCALL: target=<target> pid=<pid> op=read path=/etc/os-release fd=<fd> result=bytes:<positive count>`
- `USERSPACE FILE SYSCALL: target=<target> pid=<pid> op=close path=/etc/os-release fd=<fd> result=0`
- `USERSPACE TMP SYSCALL: target=<target> pid=<pid> op=write path=/tmp/daps-probe result=bytes:<positive count>`

The verifier requires OPEN → READ → CLOSE on the same descriptor, successful nonzero
read/write counts, matching target and PID, and all records inside the acknowledged
userspace execution window. These records must be emitted from the real syscall/VFS
implementation; do not add synthetic lines to production logs. Until kernel instrumentation
and actual userspace operations produce them, DAPS intentionally fails closed.

A passing report means these mechanical evidence requirements were met; reviewers must
still inspect provenance, QEMU/firmware configuration, disk snapshots, and per-CPU traces
before approving publication. Never manufacture these records to make the verifier pass.
