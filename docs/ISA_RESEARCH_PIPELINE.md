# ISA and operating-system research pipeline

The ISO build refreshes an advisory research catalog before compiling the boot artifacts. It checks official architecture/kernel documentation and searches GitHub public repository metadata for ISA decoders, assemblers/disassemblers, driver implementations, schedulers, firmware, syscall compatibility, and mobile OS kernels.

## Outputs

- `docs/research/isa-command-research.json`: machine-readable source and repository index, request status, timestamps, and content hashes.
- `docs/research/ISA_COMMAND_RESEARCH.md`: readable summary and safe-adoption workflow.
- `docs/research/library-import/`: optional local export folder for documentation copied from the user's ChatGPT Library.

## Run manually

```bash
python3 tools/isa/research_catalog.py
python3 tools/isa/research_catalog.py --offline
```

Set `GITHUB_TOKEN` to a GitHub token to improve search API rate limits. Do not commit tokens. To use another Library-export folder, set `CHIMERA_RESEARCH_LIBRARY_DIR=/path/to/export`.

Set `CHIMERA_ISA_RESEARCH=0` to skip network discovery during ISO builds. The research stage is best-effort: network/API failure is logged and does not stop a build that can use the existing registries.

## Scope and safety

“Deep search” is implemented as multiple targeted public GitHub repository searches plus a curated set of authoritative documentation entry points, not as a claim to crawl every repository or every page on the internet. The public GitHub API is rate-limited and search results are capped.

The build host cannot directly access the ChatGPT Library service. Export relevant documents into `docs/research/library-import/` (or configure `CHIMERA_RESEARCH_LIBRARY_DIR`) to index them alongside repository documentation.

This pipeline **does not execute remote code, copy arbitrary shell commands into the OS, or automatically add discovered mnemonics to privileged registries**. Research results require review for correctness, license, security, architecture/extension support, CPU feature detection, privilege level, and test coverage before adoption. This prevents malicious READMEs, fake opcodes, or unsafe command examples from entering the kernel or native command registry automatically.
