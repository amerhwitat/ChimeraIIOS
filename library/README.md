# Chimera II OS — Library Archive

This directory records and imports Chimera II OS research artifacts found in the ChatGPT Library.

## Policy

Library material is treated as **reference/provenance input**, not automatically as production code. Each artifact must be classified before entering a build target:

- `reference/` — source prototypes, experiments and historical code.
- `specifications/` — architecture and engineering documents.
- `research/` — research reports and design studies.
- `assets/` — diagrams and other visual material when binary import is supported.
- `archives/` — ZIP/TAR and other packaged artifacts.
- `provenance/` — inventory, source mapping and licensing notes.

Third-party or historical material must retain attribution and license information and must not silently become a linked build dependency. Proprietary binaries, ROMs, firmware, BIOS images and game data are not incorporated into executable targets.

## Imported references

- `reference/chimera_ii_8192_cpu_emulator.py` — 8192-bit RISC/CISC reference emulator.
- `reference/chimera_ii_requirements.txt` — Python reference dependencies.

## Library source set identified for Chimera II

The Library currently contains, among other artifacts, the following directly relevant documents and source packages:

- `Chimera II OS Developer Guide.txt`
- `Chimera II OS - crash dump.docx`
- `Chimera II IEEE RFC Standards Reference.pdf`
- `Chimera II Low Level Specification.pdf`
- `Chimera II OS 8192 High Low Level Technical Specification.pdf`
- `Chimera II OS Comprehensive Redesign Research Report.pdf`
- `Chimera II OS Mobile Robotics Architecture Report.pdf`
- `Chimera II OS Professional Research Book_Amer Hwitat.pdf`
- `Chimera II OS Source Blueprint v2.zip`
- `chimera_ii_os_8192_full_platform.zip`
- `chimera_ii_source.zip`
- `chimera_ii_os_web.zip`
- `chimera_ii_c_v1.0.zip`
- `chimera_ii_c_v1.0.tar.gz`
- `chimera_ii_c_v1.0_linux_x86_64.zip`
- `CPU4096-ARM-and_X86.docx`
- `CPU4096-ARM-and_X86.pdf`
- `Source-Code.pdf`
- `Complete_Research_and_Project_Knowledge_Archive.pdf`
- `color.c`
- `all-win32-2000-code.pdf`
- `AmigaGuruBook[ENG]FullSearch.txt`

## Important limitation

The ChatGPT Library contains binary PDFs, DOCX, images, videos and compressed archives. The connected GitHub contents interface available to this workflow accepts UTF-8 text files but does not provide a binary-file upload operation. Therefore binary artifacts are **inventoried and provenance-tracked here rather than falsely represented as committed binaries**. Text/source artifacts that can be safely imported through the available interface are copied into this archive.

This separation preserves the distinction between source evidence and production implementation while allowing the Chimera II repository to consume the Library as an explicit research corpus.
