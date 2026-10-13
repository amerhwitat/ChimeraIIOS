# Machine-code toolchain contract

`chimera-machine-code.py` is the front door for identifying object/executable containers and routing selected toolchain operations.

## Commands

- `identify FILE`: inspect a file header and report format, architecture, endianness, size, and SHA-256. It never decodes every instruction or asserts ISA conformance.
- `providers`: report whether selected external tools are discoverable on the current host.
- `assemble --arch ARCH -o FILE OBJECT.s`: ask Clang (or LLVM MC when a triple is supplied) to produce a relocatable object.
- `compile --arch ARCH -o FILE SOURCE.c [--language c|c++|assembler|assembler-with-cpp] [--flag FLAG ...]`: ask Clang to produce an object for a target triple. This does not imply a sysroot, linker, C runtime, or target ABI is installed.
- `disassemble FILE`: invoke LLVM objdump or GNU objdump for a recognized object/executable.
- `execute FILE [-- ARG ...]`: run only recognized formats through an installed native or explicit compatibility provider. Unknown formats are refused.

## Capability boundaries

Architecture metadata is not instruction coverage. Provider discovery is not proof that a provider supports a specific target or binary ABI. A successful compile is not an execution test. A successful emulation run is not native hardware validation.

Current format identification covers ELF, PE/COFF, DOS MZ, Mach-O/fat Mach-O, WebAssembly, UF2, Intel HEX signatures, and shebang scripts. Some formats need additional parsing before they can be considered fully validated. For example, Intel HEX checksums are not yet verified here, and Mach-O universal binaries are reported as fat containers rather than enumerating every slice.

Unknown raw bytes are not auto-classified from opcode heuristics. Pass `--arch` only when the caller already knows the intended architecture; raw bytes still do not become safe executables.

## Next conformance layers

Each architecture/profile needs its own sourced instruction definitions, bit-field decoder/encoder, operand semantics, register/flag/memory/exception effects, and reference vectors. Execution support should move from provider-required to conformance-tested only after differential tests against a trusted simulator or official test suite pass. OS process handoff and SMP acceptance are separate kernel gates.
