# Chimera II OS — Master Source Map

This document maps the Developer Guide sections to the refreshed source tree. It is the integration contract for future contributions.

| Developer Guide section | Primary source | Status |
|---|---|---|
| Boot: Spit Fire / Jasper | `boot/spitfire`, `boot/jasper`, `boot/x86/mbr` | prototype + target |
| Koronos / RegisterN / scheduler | `kernel`, `lib/registern`, `include/chimera` | host prototype |
| Spotnik / AF_XDP / Netmap | `net`, `userspace/spotnik` | interface boundary |
| VFS / TensorFS / Nucleus / Hive | `userspace/ndb`, `userspace/hive` | skeleton |
| Aurora | `userspace/aurora`, `desktop/aurora` | interface/shader prototype |
| CEF | `userspace/cef` | manifest boundary |
| Security / signing / CI | `tools`, `.github/workflows` | planned/target |
| ISA | `isa/r8192`, `isa/c8192`, `tools/isa_parser` | host emulator |
| Tests / QEMU | `tests/unit`, `tests/qemu_e2e` | host tests + target harness |
| 128D / cognitive architecture | `cognitive` | research prototype |

## Integration rule

Code belongs beside the subsystem it implements. Documentation should link to the implementation rather than duplicating large code blocks. Generated or historical source is kept separate from production-intended modules.

## Architectural separation

The machine plane executes instructions; the cognitive plane represents state, memory, knowledge and reasoning; the world plane handles I/O. The kernel provides deterministic resource control and isolation rather than embedding application-level intelligence.
