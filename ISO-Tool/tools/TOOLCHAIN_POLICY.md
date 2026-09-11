# Toolchain acquisition policy

ISO-Tool separates redistributable open-source toolchains from vendor-installed tools. NASM, LLVM and GNU components are consumed under their respective licenses; MASM is detected from an existing Visual Studio/Build Tools installation and is not redistributed. Downloaded dependencies use the profile Downloads cache and explicit installation authorization.

Every selected assembler/disassembler is recorded with backend ID, executable path and version. The registry is extensible so additional cross assemblers/disassemblers can be discovered without changing the ISO staging contract.
