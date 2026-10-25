# PE/COFF EFI application validation contract

Status: structural gate only. Passing synthetic fixtures does not prove firmware compatibility or boot.

CI must validate the DOS MZ header, bounded e_lfanew, PE signature, complete COFF and optional headers, explicit target COFF Machine, PE32/PE32+ magic, section-table and raw-file bounds, section RVA ranges, alignments, SizeOfHeaders and SizeOfImage, and a nonzero entry RVA inside an executable section. For a bootloader application the Subsystem must be EFI_APPLICATION (10); boot-service drivers (11) and runtime drivers (12) are different artifact types and must not pass this gate.

Target machine profiles include IA32 0x014c, x64 0x8664, AArch64 0xAA64, RISC-V32 0x5032, RISC-V64 0x5064, and LoongArch64 0x6264. Profiles must be explicit; the filename extension and UEFI mode do not identify the CPU ISA.

The validator is deliberately not a complete PE/COFF implementation. It does not prove relocation correctness, firmware policy compatibility, signature acceptance, or execution. A real target build, immutable artifact hash, and firmware/emulator boot trace are still required. EFI PE/COFF and kernel ELF remain separate artifacts.

References: UEFI Specification, Overview (machine and subsystem definitions); Microsoft PE/COFF format (optional-header bounds and magic).
