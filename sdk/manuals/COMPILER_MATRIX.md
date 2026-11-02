# Compiler, Interpreter, Assembler and Disassembler Matrix

The canonical, machine-readable inventory is
`toolchains/language-toolchain-catalog.json`. It covers 49 language families,
their compiler/interpreter commands, execution models, package hints, ten
assembler families, nine disassembler/binary-analysis tools, linkers and
cross-target families.

## Language coverage

| Family | Languages / toolchains |
|---|---|
| Systems | C, C++, Objective-C, Objective-C++, Rust, Go, Swift, Fortran, Ada, D, Zig, Nim, Crystal |
| Managed / JVM | Java, Kotlin, Scala, Groovy, C#, F#, Visual Basic .NET |
| Functional / scientific | Haskell, OCaml, Pascal, COBOL, Julia, R, Elixir, Erlang, Clojure, Common Lisp, Scheme, Prolog |
| Scripting / web | Python, JavaScript, TypeScript, PHP, Ruby, Perl, Lua, Tcl, PowerShell |
| Shell / data | Bash, Zsh, Fish, AWK, SQL |
| Binary / low-level | Assembly, WebAssembly |

## Assemblers and disassemblers

Assembler providers include GNU as, LLVM MC, NASM, YASM, FASM, ARM/AArch64
and RISC-V GNU assemblers, MASM (external installation), and the Chimera ISA
assembler. Disassembly and inspection providers include GNU objdump/readelf,
LLVM objdump/readobj, NDISASM, Capstone, radare2, Ghidra and Chimera ISA
disassemblers.

Linker and binary utility coverage includes GNU ld, gold, LLD, mold, wasm-ld,
ar, ranlib, nm, objcopy, strip, addr2line, c++filt, patchelf and chrpath.

## Install optional toolchains

Aurora exposes explicit optional profiles: `native-core`, `systems`,
`managed`, `scripting`, `functional-scientific`, `assembly-analysis`,
and `webassembly`.

List profiles:

```sh
tools/toolchain/install-language-profile.py --list
```

Preview packages for a profile:

```sh
tools/toolchain/install-language-profile.py systems --dry-run
```

Install only after reviewing the package plan and confirming explicitly:

```sh
sudo python3 tools/toolchain/install-language-profile.py systems --yes
```

The installer supports apt, dnf and pacman package managers. Package
availability varies by distribution/version; a missing mapping is reported
rather than silently substituted. Proprietary vendor toolchains are not
redistributed and must be installed from their vendors.

## Capability and ABI policy

A catalog entry means a provider is recognized; it does not mean the compiler
or runtime is present on the ISO or currently executable. Native execution
requires an installed compiler/runtime, matching ABI libraries and sysroot.
Cross-compilation additionally requires a supported target backend, target
sysroot and linker. WebAssembly is a virtual-machine target, not a native CPU
ABI. Chimera C8192/R8192 are experimental custom backends and are not implied
to be implemented by GCC or LLVM.

CI validates the catalog schema, package-manager profile mappings and
regression tests. Tool availability is separately detected at build/runtime.
