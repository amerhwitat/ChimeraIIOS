#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
mkdir -p "$BUILD"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(
  koronos elf64 module relocate arch_init runtime_loop scheduler thread sync timer apc dpc
  hardware nbit firmware device multiboot_modules parallel driver learning microkernel
)
for src in "${sources[@]}"; do
  "$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/$src.cpp" -o "$BUILD/$src.o"
done
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/nbit_note.cpp" -DCHIMERA_NBIT_IMAGE_BITS=64 -o "$BUILD/nbit-note-64.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/virtio.cpp" -o "$BUILD/virtio-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pc-display.cpp" -o "$BUILD/display-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pci-generic.cpp" -o "$BUILD/pci-generic-driver.o"

"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/entry.asm" -o "$BUILD/entry.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/io.asm" -o "$BUILD/io.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/mode_switch.asm" -o "$BUILD/mode_switch.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=(
  "$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o"
  "$BUILD/koronos.o" "$BUILD/elf64.o" "$BUILD/module.o" "$BUILD/relocate.o"
  "$BUILD/arch_init.o" "$BUILD/runtime_loop.o" "$BUILD/scheduler.o" "$BUILD/thread.o"
  "$BUILD/sync.o" "$BUILD/timer.o" "$BUILD/apc.o" "$BUILD/dpc.o" "$BUILD/hardware.o"
  "$BUILD/nbit.o" "$BUILD/firmware.o" "$BUILD/device.o" "$BUILD/multiboot_modules.o"
  "$BUILD/parallel.o" "$BUILD/driver.o" "$BUILD/learning.o" "$BUILD/microkernel.o"
  "$BUILD/virtio-driver.o" "$BUILD/display-driver.o" "$BUILD/pci-generic-driver.o" "$BUILD/module-test.o"
)
"$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" -o "$BUILD/koronos.elf"

if command -v readelf >/dev/null 2>&1; then
  readelf -h "$BUILD/koronos.elf" | grep -Eq 'Class:[[:space:]]+ELF64' || { echo "ERROR: Koronos is not ELF64" >&2; exit 1; }
fi
if command -v nm >/dev/null 2>&1; then
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall)
  for symbol in "${required_symbols[@]}"; do
    nm -g "$BUILD/koronos.elf" | grep -Eq "[[:space:]]${symbol}$" || { echo "ERROR: $symbol is not linked" >&2; exit 1; }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf32-compatible-container.elf"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" \
    "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos microkernel IPC + scheduler + sync + timers + APC/DPC + hardware/firmware + drivers + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"
