#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
mkdir -p "$BUILD"
CXX="${CXX:-g++}"
NASM="${NASM:-nasm}"
LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/koronos.cpp" -o "$BUILD/koronos.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/elf64.cpp" -o "$BUILD/elf64.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/module.cpp" -o "$BUILD/module.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/arch_init.cpp" -o "$BUILD/arch_init.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/entry.asm" -o "$BUILD/entry.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/io.asm" -o "$BUILD/io.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/mode_switch.asm" -o "$BUILD/mode_switch.o"
"$LD" -nostdlib -z max-page-size=0x1000 -T "$ROOT/kernel/arch/x86_64/koronos.ld" "$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/koronos.o" "$BUILD/elf64.o" "$BUILD/module.o" "$BUILD/arch_init.o" -o "$BUILD/koronos.elf"
printf "Koronos ELF64: %s\n" "$BUILD/koronos.elf"