#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
mkdir -p "$BUILD"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features)
for src in "${sources[@]}"; do
  "$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/$src.cpp" -o "$BUILD/$src.o"
done
"$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS=64 -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-64.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/virtio.cpp" -o "$BUILD/virtio-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pc-display.cpp" -o "$BUILD/display-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pci-generic.cpp" -o "$BUILD/pci-generic-driver.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/entry.asm" -o "$BUILD/entry.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/io.asm" -o "$BUILD/io.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/mode_switch.asm" -o "$BUILD/mode_switch.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o")
for src in "${sources[@]}"; do link_objects+=("$BUILD/$src.o"); done
link_objects+=("$BUILD/virtio-driver.o" "$BUILD/display-driver.o" "$BUILD/pci-generic-driver.o" "$BUILD/module-test.o")
for obj in "${link_objects[@]}"; do
  [[ -f "$obj" ]] || { echo "ERROR: required Koronos link object is missing: $obj" >&2; exit 1; }
done

if command -v nm >/dev/null 2>&1; then
  nm -a --defined-only "$BUILD/multiboot_modules.o" | awk '$NF == "chimera_multiboot_scan" { found=1 } END { exit !found }' || {
    echo "ERROR: chimera_multiboot_scan is absent from multiboot_modules.o" >&2; nm -a "$BUILD/multiboot_modules.o" >&2 || true; exit 1;
  }
fi

"$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" -o "$BUILD/koronos.elf"
if command -v readelf >/dev/null 2>&1; then
  readelf -h "$BUILD/koronos.elf" | grep -Eq 'Class:[[:space:]]+ELF64' || { echo "ERROR: Koronos is not ELF64" >&2; exit 1; }
fi
if command -v nm >/dev/null 2>&1; then
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_kore_bootstrap chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
printf '%s\n' 'Native OOP object model + SMP-safe scheduler + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"
