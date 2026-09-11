# Chimera II OS Library Provenance Index

Generated from the user's ChatGPT Library search on 2026-09-11. The Library contains 574 listed lines in the current inventory response and substantially more artifacts than the Chimera-specific subset below.

## Chimera-specific artifacts identified

| Artifact | Type | Intended repository role |
|---|---|---|
| Chimera II OS Developer Guide.txt | text | consolidated developer/spec reference |
| Chimera II OS - crash dump.docx | document | source scaffold and implementation notes |
| Chimera_II_IEEE_RFC_Standards_Reference.pdf | PDF | standards/reference material |
| Chimera_II_Low_Level_Specification.pdf | PDF | low-level architecture |
| Chimera_II_OS_8192_High_Low_Level_Technical_Specification.pdf | PDF | CPU/OS technical specification |
| Chimera_II_OS_Comprehensive_Redesign_Research_Report.pdf | PDF | architecture, provenance and implementation roadmap |
| Chimera_II_OS_Mobile_Robotics_Architecture_Report.pdf | PDF | mobile/robotics architecture |
| Chimera_II_OS_Professional_Research_Book_Amer_Hwitat.pdf | PDF | consolidated research book |
| Chimera_II_OS_Source_Blueprint_v2.zip | archive | source blueprint |
| chimera_ii_os_8192_full_platform.zip | archive | platform source package |
| chimera_ii_source.zip | archive | source package |
| chimera_ii_os_web.zip | archive | web runtime package |
| chimera_ii_c_v1.0.zip | archive | C implementation package |
| chimera_ii_c_v1.0.tar.gz | archive | C implementation package |
| chimera_ii_c_v1.0_linux_x86_64.zip | archive | Linux x86-64 package |
| chimera_ii_8192_cpu_emulator.py | Python | CPU/ISA reference implementation |
| chimera_ii_requirements.txt | text | Python reference dependencies |
| CPU4096-ARM-and_X86.docx | document | 4096-bit architecture reference |
| CPU4096-ARM-and_X86.pdf | PDF | 4096-bit architecture reference |
| Source-Code.pdf | PDF | source blueprint/reference |
| Complete_Research_and_Project_Knowledge_Archive.pdf | PDF | consolidated knowledge archive |
| color.c | C source | historical Windows color-management reference |
| all-win32-2000-code.pdf | PDF | historical Win32 reference |
| AmigaGuruBook[ENG]FullSearch.txt | text | Amiga/legacy compatibility research |
| Chimera II Web Runtime & Desktop Integration | research report | web/desktop integration |

## Design consequences captured from the Library

1. Keep Computer Edition/Koronos and Mobile Edition/Mobile Microkernel as separate kernel targets.
2. Keep R8192/C8192 as a configurable virtual architecture rather than claiming existing 8192-bit silicon.
3. Keep cognitive/AI processing above the microkernel.
4. Preserve capability isolation, IOMMU-aware DMA, zero-copy IPC/networking and verified boot as explicit interfaces.
5. Track third-party source licenses before any source is made part of a production build.
6. Keep proprietary firmware, ROMs, BIOS images and game data outside the repository unless redistribution rights are established.

## Source evidence

The Library's comprehensive redesign report explicitly describes the project as a research/engineering blueprint, identifies the source-code deliverable as a clean-room scaffold, and states that arbitrary Linux/Windows/emulator source should not be merged without licensing and compatibility assessment. This index follows that rule.
