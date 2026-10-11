#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: kernel/build-koronos.sh

Usage:
  kernel/build-koronos.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Custom N-bit build profiles:
  CHIMERA_NBIT_EXTRA_WIDTHS="13 8193 100003" kernel/build-koronos.sh

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
python3 -m json.tool "$ROOT/isa/isa_database.json" >/dev/null
python3 -m json.tool "$ROOT/isa/gpu_isa_registry.json" >/dev/null
python3 "$ROOT/tools/isa/generate_registry.py"
# Keep an auditable, reproducible snapshot of the CPU/GPU ISA inputs used by this build.
python3 "$ROOT/tools/isa/chimera_isa_convert.py" inventory > "$BUILD/isa-inventory.json"
sha256sum "$ROOT/isa/isa_database.json" "$ROOT/isa/gpu_isa_registry.json" > "$BUILD/isa-inputs.sha256"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(physmem dma dbus_compat koronos elf64 module relocate arch_init runtime runtime_loop scheduler process thread sync timer apc dpc hardware nbit nbit_runtime nbit_vm firmware device multiboot_modules parallel user_mode nbit_cache driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model elf_loader ipc)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/user_mode.asm" -o "$BUILD/user-mode.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o" "$BUILD/user-mode.o")
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

# Build a tiny freestanding ET_EXEC payload used to verify the real ring-3
# transition on every normal/live/install boot path. It is deliberately not
# presented as the complete Aurora userspace; it proves the kernel-to-user ABI.
"$CXX" "${CXXFLAGS[@]}" -mcmodel=large -fno-asynchronous-unwind-tables -fno-unwind-tables -c "$ROOT/kernel/userland/init.cpp" -o "$BUILD/chimera-user-init.o"
"$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/user_init.ld" "$BUILD/chimera-user-init.o" -o "$BUILD/chimera-user-init.elf"
if command -v readelf >/dev/null 2>&1; then
  readelf -h "$BUILD/chimera-user-init.elf" | grep -Eq 'Type:[[:space:]]+EXEC' || { echo "ERROR: user init payload is not ET_EXEC" >&2; exit 1; }
  readelf -l "$BUILD/chimera-user-init.elf" | grep -q 'LOAD' || { echo "ERROR: user init payload has no PT_LOAD segment" >&2; exit 1; }
fi

if command -v readelf >/dev/null 2>&1; then
  readelf -h "$BUILD/koronos.elf" | grep -Eq 'Class:[[:space:]]+ELF64' || { echo "ERROR: Koronos is not ELF64" >&2; exit 1; }
fi
if command -v nm >/dev/null 2>&1; then
  required_symbols=(chimera_dma_device_init chimera_dma_map_physical chimera_dma_unmap chimera_dma_translate_nbit_width chimera_dbus_compat_validate chimera_physmem_init chimera_physmem_alloc_page chimera_physmem_free_page chimera_x86_64_user_mode_init chimera_x86_64_user_loader_ops chimera_x86_64_user_range_valid chimera_x86_64_enter_user koronos_idle_loop chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_nbit_set_default_profile chimera_nbit_set_default_profile_ex chimera_nbit_process_init_default chimera_nbit_get_capabilities chimera_nbit_process_init_chimera chimera_nbit_process_init_physical_native chimera_nbit_word_add chimera_nbit_word_subtract chimera_nbit_batch_add chimera_nbit_vm_initialize chimera_nbit_vm_set_cache chimera_nbit_vm_run chimera_nbit_cache_initialize chimera_nbit_cache_invalidate chimera_nbit_process_init chimera_nbit_process_set_mode chimera_nbit_process_set_compatibility chimera_nbit_process_unregister chimera_nbit_process_get chimera_nbit_process_snapshot chimera_nbit_registry_get_snapshot chimera_nbit_ipc_prepare chimera_nbit_ipc_validate chimera_nbit_ipc_copy_payload chimera_ipc_service_init chimera_ipc_endpoint_bind chimera_ipc_endpoint_unbind chimera_ipc_send chimera_ipc_receive chimera_ipc_cancel chimera_ipc_process_exit chimera_ipc_queued_messages chimera_process_set_execution_mode chimera_process_set_chimera_mode chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_elf_load_and_enter chimera_process_discard_admitted chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider memset memcpy memmove)
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
printf '%s\n' 'Protected-process admission/load-plan boundary + Native OOP object model + SMP-safe scheduler + syscall/interrupt compatibility + parallel dispatch linked.'
cp "$BUILD/koronos.elf" "$BUILD/koronos.elf64"
mkdir -p "$BUILD/nbit"
NBIT_WIDTHS=(8 16 32 64 128 256 512 1024 2048 4096 8192)
# Add any positive uint32 width as a build profile, e.g. CHIMERA_NBIT_EXTRA_WIDTHS="13 8193 100003".
if [[ -n "${CHIMERA_NBIT_EXTRA_WIDTHS:-}" ]]; then
  read -r -a extra_widths <<< "$CHIMERA_NBIT_EXTRA_WIDTHS"
  for bits in "${extra_widths[@]}"; do
    [[ "$bits" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: invalid extra N-bit width: $bits" >&2; exit 1; }
    (( bits <= 4294967295 )) || { echo "ERROR: N-bit width exceeds uint32 ABI limit: $bits" >&2; exit 1; }
    NBIT_WIDTHS+=("$bits")
  done
fi
declare -A seen_widths=()
for bits in "${NBIT_WIDTHS[@]}"; do
  [[ -n "${seen_widths[$bits]:-}" ]] && continue
  seen_widths[$bits]=1
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"