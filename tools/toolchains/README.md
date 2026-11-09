# Open toolchain bootstrap

Use bash tools/toolchains/bootstrap-open-toolchains.sh list to inspect the reviewed package set,
install to install packages available from the host package manager, and verify to report
available tools. Debian/Ubuntu installs only packages present in configured repositories;
missing targets are reported rather than represented as installed.

The package set includes GCC/G++, Clang/LLVM, GNU binutils, NASM/YASM, GDB/GDB multiarch,
LLDB, Valgrind, CMake/Ninja and QEMU user-mode cross-architecture runners. This is a
package bootstrap, not a claim that every listed ISA has a complete native compiler backend.
