# Provenance and source-import policy

## Inputs used in the 2026 consolidation

1. **Chimera II OS Developer Guide** — structural baseline for boot, kernel, networking, filesystems/data, graphics, emulation, security/CI, ISA tooling and tests.
2. **Pasted markdown architecture** — expanded R8192/C8192, 128D state engine, cognitive/world planes, knowledge/memory, autonomous-agent boundaries, distributed Chimera and visualization concepts.
3. **W2K-ASM** — historical assembly corpus containing Alpha, PowerPC and x86/Windows-era routines. It is reference material only and must not be represented as newly authored Chimera code.

## Attribution boundary

The refreshed source files under `include/`, `kernel/`, `isa/`, `cognitive/`, `net/`, `userspace/`, and `boot/` are newly organized prototype implementations derived from the project specifications. They are not claims that the historical source is authored by the project.

## Historical W2K-ASM

The supplied W2K-ASM file is approximately 26 MB and is too large for the connected GitHub text-write interface used in this session to safely transfer verbatim. The repository therefore contains `docs/W2K-ASM_IMPORT.md` and an import helper rather than falsely claiming the complete corpus was uploaded. When working locally, copy the supplied file into `legacy/w2k-asm/W2K-ASM.txt`, calculate its SHA-256, and keep its original licensing/header provenance.

## Demo sources

The two live demo URLs are references, not proof of source availability. If an exported source snapshot is obtained, import it under `demos/` and review licenses, generated assets and dependencies before merging.
