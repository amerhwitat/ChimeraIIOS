# Binary inspection and reviewed runtime selection

- \`tools/inspect-binary-headers.py\` parses ELF, PE/COFF, Mach-O thin/fat, DOS MZ, Java class, WebAssembly and ZIP/JAR headers. It never executes input.
- \`tools/run-compatible-binary.py FILE\` inspects only.
- Add \`--dry-run\` to see the selected runtime command.
- Add \`--run\` to execute explicitly; use \`--sysroot\` for QEMU user-mode Linux binaries.

The runner uses native Linux/Windows/macOS execution when the host matches, QEMU user-mode
for supported foreign Linux ELF architectures, Wine for Windows PE on non-Windows hosts,
DOSBox for DOS MZ, and Wasmtime/Wasmer for WebAssembly. It refuses unsupported Mach-O on
Linux rather than pretending CPU emulation supplies macOS system libraries.

Only run trusted binaries. This tool does not bulk-download third-party executables, bypass
signatures, or hide whether a compatibility runtime is being used. It does not provide an
OS sandbox; use a disposable VM/container for untrusted programs.
