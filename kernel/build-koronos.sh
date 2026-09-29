#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
mkdir -p "$BUILD"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/koronos.cpp" -o "$BUILD/koronos.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/elf64.cpp" -o "$BUILD/elf64.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/module.cpp" -o "$BUILD/module.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/relocate.cpp" -o "$BUILD/relocate.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/arch_init.cpp" -o "$BUILD/arch_init.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/runtime_loop.cpp" -o "$BUILD/runtime_loop.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/scheduler.cpp" -o "$BUILD/scheduler.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/thread.cpp" -o "$BUILD/thread.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/sync.cpp" -o "$BUILD/sync.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/timer.cpp" -o "$BUILD/timer.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/apc.cpp" -o "$BUILD/apc.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/dpc.cpp" -o "$BUILD/dpc.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/hardware.cpp" -o "$BUILD/hardware.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/nbit.cpp" -o "$BUILD/nbit.o"
"$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS=64 -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-64.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/firmware.cpp" -o "$BUILD/firmware.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/device.cpp" -o "$BUILD/device.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/multiboot_modules.cpp" -o "$BUILD/multiboot_modules.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/parallel.cpp" -o "$BUILD/parallel.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/driver.cpp" -o "$BUILD/driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/core/learning.cpp" -o "$BUILD/learning.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/virtio.cpp" -o "$BUILD/virtio-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pc-display.cpp" -o "$BUILD/display-driver.o"
"$CXX" "${CXXFLAGS[@]}" -c "$ROOT/kernel/drivers/builtin/pci-generic.cpp" -o "$BUILD/pci-generic-driver.o"

"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/entry.asm" -o "$BUILD/entry.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/io.asm" -o "$BUILD/io.o"
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/mode_switch.asm" -o "$BUILD/mode_switch.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

"$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" \
  "$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/koronos.o" "$BUILD/elf64.o" \
  "$BUILD/module.o" "$BUILD/relocate.o" "$BUILD/arch_init.o" "$BUILD/runtime_loop.o" \
  "$BUILD/scheduler.o" "$BUILD/thread.o" "$BUILD/sync.o" "$BUILD/timer.o" "$BUILD/apc.o" "$BUILD/dpc.o" \
  "$BUILD/hardware.o" "$BUILD/nbit.o" "$BUILD/multiboot_modules.o" "$BUILD/parallel.o" "$BUILD/driver.o" \
  "$BUILD/learning.o" "$BUILD/virtio-driver.o" "$BUILD/display-driver.o" "$BUILD/pci-generic-driver.o" "$BUILD/module-test.o" \
  -o "$BUILD/koronos.elf"

if command -v readelf >/dev/null 2>&1; then
  readelf -h "$BUILD/koronos.elf" | grep -Eq 'Class:[[:space:]]+ELF64' || { echo "ERROR: Koronos is not an ELF64 image" >&2; exit 1; }
fi
if command -v nm >/dev/null 2>&1; then
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]koronos_idle_loop$' || { echo "ERROR: koronos_idle_loop is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_multiboot_scan$' || { echo "ERROR: Multiboot2 module scanner is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_thread_create$' || { echo "ERROR: thread facade is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_wait_one$' || { echo "ERROR: synchronization wait foundation is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_timer_tick$' || { echo "ERROR: timer foundation is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_apc_deliver$' || { echo "ERROR: APC foundation is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_dpc_run$' || { echo "ERROR: DPC foundation is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_hardware_probe$' || { echo "ERROR: hardware probe is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_nbit_init
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf "Koronos ELF64: %s\\n" "$BUILD/koronos.elf"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" \
    "$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/koronos.o" "$BUILD/elf64.o" \
    "$BUILD/module.o" "$BUILD/relocate.o" "$BUILD/arch_init.o" "$BUILD/runtime_loop.o" \
    "$BUILD/scheduler.o" "$BUILD/thread.o" "$BUILD/sync.o" "$BUILD/timer.o" "$BUILD/apc.o" "$BUILD/dpc.o" \
    "$BUILD/hardware.o" "$BUILD/nbit.o" "$BUILD/firmware.o" "$BUILD/device.o" "$BUILD/multiboot_modules.o" "$BUILD/parallel.o" "$BUILD/driver.o" \
    "$BUILD/learning.o" "$BUILD/virtio-driver.o" "$BUILD/display-driver.o" "$BUILD/pci-generic-driver.o" "$BUILD/module-test.o" "$BUILD/nbit-note-$bits.o" \
    -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf"
printf "Koronos ELF64 + generic ELF + N-bit ELF metadata variants generated under %s/nbit\\n" "$BUILD"
printf "Koronos runtime check: scheduler + threads + synchronization + timers + APC/DPC + firmware probe + hardware/device enumeration + N-bit runtime + driver probe manager + Multiboot2 registry + installer bootstrap linked and ELF64 verified\\n"
 || { echo "ERROR: N-bit runtime is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_firmware_probe
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf "Koronos ELF64: %s\\n" "$BUILD/koronos.elf"
printf "Koronos runtime check: scheduler + threads + synchronization + timers + APC/DPC + hardware probe + N-bit runtime + Multiboot2 registry + installer bootstrap linked and ELF64 verified\\n"
 || { echo "ERROR: firmware probe is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_hardware_enumerate_devices
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf "Koronos ELF64: %s\\n" "$BUILD/koronos.elf"
printf "Koronos runtime check: scheduler + threads + synchronization + timers + APC/DPC + hardware probe + N-bit runtime + Multiboot2 registry + installer bootstrap linked and ELF64 verified\\n"
 || { echo "ERROR: hardware enumeration is not linked" >&2; exit 1; }
  nm -g "$BUILD/koronos.elf" | grep -Eq '[[:space:]]chimera_driver_probe_all
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf "Koronos ELF64: %s\\n" "$BUILD/koronos.elf"
printf "Koronos runtime check: scheduler + threads + synchronization + timers + APC/DPC + hardware probe + N-bit runtime + Multiboot2 registry + installer bootstrap linked and ELF64 verified\\n"
 || { echo "ERROR: driver probe manager is not linked" >&2; exit 1; }
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf "Koronos ELF64: %s\\n" "$BUILD/koronos.elf"
printf "Koronos runtime check: scheduler + threads + synchronization + timers + APC/DPC + hardware probe + N-bit runtime + Multiboot2 registry + installer bootstrap linked and ELF64 verified\\n"
