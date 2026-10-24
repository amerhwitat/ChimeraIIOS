#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: kernel/build-koronos.sh

Usage:
  kernel/build-koronos.sh [options] [arguments]

Options:
  -h, --help                    Show this help and exit successfully.
  --system-block-size BYTES     Set the kernel system/block I/O size.
  --system-block-size=BYTES     Equivalent form.

System block size defaults to 4096 bytes. Valid values are powers of two from
512 through 65536 bytes. KORONOS_SYSTEM_BLOCK_SIZE sets the same default when
the command-line option is omitted.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/koronos/x86_64"
SYSTEM_BLOCK_SIZE="${KORONOS_SYSTEM_BLOCK_SIZE:-4096}"
while (($#)); do
  case "$1" in
    --system-block-size)
      if (($# < 2)); then echo "ERROR: --system-block-size requires a byte count" >&2; exit 2; fi
      SYSTEM_BLOCK_SIZE="$2"
      shift 2
      ;;
    --system-block-size=*)
      SYSTEM_BLOCK_SIZE="${1#*=}"
      shift
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      echo "Use --help for supported options." >&2
      exit 2
      ;;
  esac
done
if [[ ! "$SYSTEM_BLOCK_SIZE" =~ ^[0-9]+$ ]]; then echo "ERROR: system block size must be an integer power of two (512..65536)" >&2; exit 2; fi
SYSTEM_BLOCK_SIZE=$((10#$SYSTEM_BLOCK_SIZE))
if (( SYSTEM_BLOCK_SIZE < 512 || SYSTEM_BLOCK_SIZE > 65536 || (SYSTEM_BLOCK_SIZE & (SYSTEM_BLOCK_SIZE - 1)) != 0 )); then echo "ERROR: KORONOS_SYSTEM_BLOCK_SIZE must be a power of two between 512 and 65536 bytes" >&2; exit 2; fi
mkdir -p "$BUILD"
bash -n "$ROOT/tools/build-production-init-elfs.sh"
python3 "$ROOT/tools/tests/test_koronos_build_script_contract.py"
python3 "$ROOT/tools/tests/test_validate_native_init_elf.py"
python3 "$ROOT/tools/tests/test_native_init_packaging_contract.py"
python3 "$ROOT/tools/tests/test_native_init_launch_gate.py"
python3 "$ROOT/tools/tests/test_production_closeout_daps.py"
python3 "$ROOT/tools/tests/test_target_init_payload_binding.py"
HOST_CXX="${HOST_CXX:-g++}"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/initramfs_cpio.cpp" "$ROOT/kernel/tests/initramfs_cpio_test.cpp" -o "$BUILD/initramfs-cpio-test"
"$BUILD/initramfs-cpio-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/gzip.cpp" "$ROOT/kernel/tests/gzip_decoder_test.cpp" -o "$BUILD/gzip-decoder-test"
"$BUILD/gzip-decoder-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/initramfs_cpio.cpp" "$ROOT/kernel/core/gzip.cpp" "$ROOT/kernel/core/initramfs_ingest.cpp" "$ROOT/kernel/tests/initramfs_ingest_test.cpp" -o "$BUILD/initramfs-ingest-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/initramfs_cpio.cpp" "$ROOT/kernel/core/ramfs.cpp" "$ROOT/kernel/tests/ramfs_test.cpp" -o "$BUILD/ramfs-test"
"$BUILD/ramfs-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/block_device.cpp" "$ROOT/kernel/core/iso9660.cpp" "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/tests/block_device_iso9660_test.cpp" -o "$BUILD/block-device-iso9660-test"
"$BUILD/block-device-iso9660-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/tests/vfs_test.cpp" -o "$BUILD/vfs-test"
"$BUILD/vfs-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/core/tmpfs.cpp" "$ROOT/kernel/tests/tmpfs_test.cpp" -o "$BUILD/tmpfs-test"
"$BUILD/tmpfs-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/swap.cpp" "$ROOT/kernel/tests/swap_test.cpp" -o "$BUILD/swap-test"
"$BUILD/swap-test"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/block_device.cpp" "$ROOT/kernel/core/swap.cpp" \
  "$ROOT/kernel/core/swap_block_device.cpp" "$ROOT/kernel/tests/swap_block_device_test.cpp" \
  -o "$BUILD/swap-block-device-test"
"$BUILD/swap-block-device-test"
"$BUILD/initramfs-ingest-test"
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-DKORONOS_SYSTEM_BLOCK_SIZE=$SYSTEM_BLOCK_SIZE -ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(block_device iso9660 koronos elf64 module relocate arch_init runtime runtime_loop scheduler process process_loader thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model frame_allocator address_space swap swap_block_device initramfs_cpio gzip initramfs_ingest ramfs vfs tmpfs target_launch)
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
"$NASM" -f elf64 "$ROOT/kernel/arch/x86_64/user_entry.asm" -o "$BUILD/user-entry.o"
"$NASM" -f elf64 "$ROOT/kernel/modules/koronos_test_module.asm" -o "$BUILD/module-test.o"

link_objects=("$BUILD/entry.o" "$BUILD/io.o" "$BUILD/mode_switch.o" "$BUILD/interrupts.o" "$BUILD/user-entry.o")
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
  required_symbols=(koronos_idle_loop koronos_system_block_size_get chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_process_reap chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider memset memcpy memmove koronos_frame_allocator_init koronos_frame_alloc koronos_frame_alloc_contiguous koronos_frame_free koronos_frame_free_contiguous koronos_frame_free_count koronos_vm_frame_alloc koronos_vm_frame_alloc_contiguous koronos_vm_frame_retain koronos_vm_frame_release koronos_vm_frame_release_contiguous koronos_vm_frame_refcount koronos_swap_init koronos_swap_init_block_extent koronos_swap_store koronos_swap_load koronos_swap_release koronos_swap_get_snapshot koronos_swap_self_test koronos_address_space_register_tlb_shootdown koronos_address_space_map koronos_address_space_unmap koronos_address_space_protect koronos_address_space_query koronos_address_space_vma_query koronos_address_space_vma_set_backing koronos_address_space_evict_one koronos_address_space_page_fault_fastpath koronos_address_space_handle_page_fault koronos_address_space_pin koronos_address_space_unpin koronos_address_space_init koronos_address_space_ready koronos_address_space_self_test koronos_address_space_loader_ops koronos_address_space_root koronos_address_space_validate_user_range koronos_address_space_count koronos_user_entry_init koronos_arch_enter_user koronos_user_page_fault_abort koronos_syscall_entry koronos_syscall_user_dispatch koronos_console_write_user koronos_launch_selected_userspace koronos_target_note_user_write koronos_target_userspace_ready koronos_target_note_user_syscall koronos_target_validate_syscall_context koronos_target_active_pid koronos_target_active_address_space koronos_target_fs_open koronos_target_fs_read koronos_target_fs_write koronos_target_fs_close koronos_target_fs_seek chimera_vfs_init chimera_vfs_mount chimera_vfs_open chimera_vfs_read chimera_vfs_write chimera_vfs_seek chimera_vfs_close chimera_vfs_close_process chimera_tmpfs_create chimera_tmpfs_destroy chimera_tmpfs_vfs_ops koronos_target_log chimera_gzip_decompress_bounded chimera_initramfs_prepare_newc chimera_cpio_validate_newc)
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
for bits in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
  "$CXX" "${CXXFLAGS[@]}" -DCHIMERA_NBIT_IMAGE_BITS="$bits" -c "$ROOT/kernel/core/nbit_note.cpp" -o "$BUILD/nbit-note-$bits.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/kernel/arch/x86_64/koronos.ld" "${link_objects[@]}" "$BUILD/nbit-note-$bits.o" -o "$BUILD/nbit/koronos-nbit-$bits.elf"
done
printf 'Koronos ELF64: %s\n' "$BUILD/koronos.elf"
printf 'Koronos + native Kore + OOP object model + SMP-safe scheduler + hardware/firmware + drivers + syscall/interrupt compatibility + N-bit runtime linked.\n'

# Build target-specific, high-address ring-3 acceptance probes. These are test
# payloads, not production shells or installer implementations.
USER_CC="${CC:-gcc}"
for target in live installer recovery; do
  "$USER_CC" -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -fno-builtin \
    -fno-stack-protector -fno-pic -fno-pie -mcmodel=large -mno-red-zone -mno-sse -mno-mmx -msoft-float \
    -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -D"CHIMERA_TARGET_${target^^}"=1 \
    -c "$ROOT/kernel/tests/user_init_smoke.c" -o "$BUILD/user-init-${target}.o"
  "$LD" -nostdlib -z max-page-size=0x1000 --build-id=none \
    -T "$ROOT/kernel/tests/user_init_smoke.ld" \
    "$BUILD/user-init-${target}.o" -o "$BUILD/user-init-${target}.elf"
  readelf -h "$BUILD/user-init-${target}.elf" | grep -Eq 'Type:[[:space:]]+EXEC' || {
    echo "ERROR: user-init-${target}.elf is not ET_EXEC" >&2; exit 1;
  }
  readelf -lW "$BUILD/user-init-${target}.elf" | grep -Eq 'LOAD.*R E' || {
    echo "ERROR: user-init-${target}.elf has no read/execute PT_LOAD" >&2; exit 1;
  }
done

# A deliberately non-cooperative user process validates that the hardware
# timer IRQ returns to the kernel without requiring a syscall or voluntary exit.
"$USER_CC" -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -fno-builtin \
  -fno-stack-protector -fno-pic -fno-pie -mcmodel=large -mno-red-zone -mno-sse -mno-mmx -msoft-float \
  -fno-asynchronous-unwind-tables -fno-unwind-tables \
  -DCHIMERA_TARGET_LIVE=1 -DCHIMERA_TEST_HANG=1 \
  -c "$ROOT/kernel/tests/user_init_smoke.c" -o "$BUILD/user-init-timeout.o"
"$LD" -nostdlib -z max-page-size=0x1000 --build-id=none \
  -T "$ROOT/kernel/tests/user_init_smoke.ld" \
  "$BUILD/user-init-timeout.o" -o "$BUILD/user-init-timeout.elf"
readelf -lW "$BUILD/user-init-timeout.elf" | grep -Eq 'LOAD.*R E' || {
  echo "ERROR: user-init-timeout.elf has no read/execute PT_LOAD" >&2; exit 1;
}
printf 'Built non-cooperative userspace timeout probe: %s/user-init-timeout.elf\n' "$BUILD"
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"