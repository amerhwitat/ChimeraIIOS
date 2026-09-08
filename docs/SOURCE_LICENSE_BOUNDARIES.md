# Source and license boundaries

Chimera II studies public ISA specifications and Linux architecture while keeping external source trees separate.

- RISC-V specifications are publicly available and the RISC-V ISA manual repository is CC-BY-4.0: https://github.com/riscv/riscv-isa-manual
- Intel publishes x86/x86-64 architecture and instruction references through the Software Developer Manuals: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
- Arm publishes A64 instruction descriptions and architecture reference material: https://developer.arm.com/documentation/ddi0487/latest
- Linux source is GPL-2.0-only. It should remain an external reference/dependency unless individual files are deliberately incorporated with their required notices.

The Chimera compatibility implementation therefore contains original normalization and decoder code, architecture maps, and links to canonical specifications rather than copied manuals or wholesale Linux source.
