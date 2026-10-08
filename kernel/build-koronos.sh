#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: kernel/build-koronos.sh

Usage:
  kernel/build-koronos.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
mkdir -p "$BUILD"
# Canonical boot contract: retain the current Koronos bootstrap stack. The
# attached legacy implementation enlarged this to 1 MiB; that change is not
# part of the canonical pipeline and must not silently return.
ENTRY_ASM="$ROOT/kernel/arch/x86_64/entry.asm"
grep -qE '^stack32_bottom: resb 65536
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 32-bit Koronos boot stack changed." >&2; exit 2; }
grep -qE '^stack64_bottom: resb 262144
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 64-bit Koronos boot stack must remain 256 KiB." >&2; exit 2; }
! grep -qE '^stack64_bottom: resb 1048576
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: obsolete 1 MiB Koronos boot-stack change detected." >&2; exit 2; }
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 32-bit Koronos boot stack changed." >&2; exit 2; }
grep -qE '^stack64_bottom: resb 262144
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 32-bit Koronos boot stack changed." >&2; exit 2; }
grep -qE '^stack64_bottom: resb 262144
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 64-bit Koronos boot stack must remain 256 KiB." >&2; exit 2; }
! grep -qE '^stack64_bottom: resb 1048576
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: obsolete 1 MiB Koronos boot-stack change detected." >&2; exit 2; }
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 64-bit Koronos boot stack must remain 256 KiB." >&2; exit 2; }
! grep -qE '^stack64_bottom: resb 1048576
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 32-bit Koronos boot stack changed." >&2; exit 2; }
grep -qE '^stack64_bottom: resb 262144
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 64-bit Koronos boot stack must remain 256 KiB." >&2; exit 2; }
! grep -qE '^stack64_bottom: resb 1048576
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: obsolete 1 MiB Koronos boot-stack change detected." >&2; exit 2; }
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: obsolete 1 MiB Koronos boot-stack change detected." >&2; exit 2; }
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 32-bit Koronos boot stack changed." >&2; exit 2; }
grep -qE '^stack64_bottom: resb 262144
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: canonical 64-bit Koronos boot stack must remain 256 KiB." >&2; exit 2; }
! grep -qE '^stack64_bottom: resb 1048576
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD" "$ENTRY_ASM" || { echo "ERROR: obsolete 1 MiB Koronos boot-stack change detected." >&2; exit 2; }
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model watchdog)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/interrupts.asm" -o "$BUILD/interrupts.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o")
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
  required_symbols=(koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider chimera_watchdog_init chimera_watchdog_register chimera_watchdog_heartbeat chimera_watchdog_tick chimera_watchdog_mark_recovering chimera_watchdog_get chimera_watchdog_expired_count chimera_watchdog_restart_count memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Service orchestration online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[ABI ] Compatibility syscall/interrupt registry ready' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: compatibility ABI bootstrap is missing from Koronos ELF" >&2; exit 1; }

auto_banner=''
grep -aF '[WDOG] Watchdog ABI online' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: watchdog bootstrap is missing from Koronos ELF" >&2; exit 1; }

printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"