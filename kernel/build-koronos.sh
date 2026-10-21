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
# Run service lifecycle regression tests before the freestanding build.
HOST_CXX="${HOST_CXX:-g++}"
SERVICE_TEST="$BUILD/service-lifecycle-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/service.cpp" "$ROOT/kernel/tests/service_lifecycle_test.cpp" \
  -o "$SERVICE_TEST"
"$SERVICE_TEST"
rm -f "$SERVICE_TEST"
MULTIBOOT_TEST="$BUILD/multiboot-modules-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/multiboot_modules.cpp" "$ROOT/kernel/tests/multiboot_modules_test.cpp" \
  -o "$MULTIBOOT_TEST"
"$MULTIBOOT_TEST"
rm -f "$MULTIBOOT_TEST"
CPIO_TEST="$BUILD/cpio-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/cpio.cpp" "$ROOT/kernel/tests/cpio_test.cpp" \
  -o "$CPIO_TEST"
"$CPIO_TEST"
rm -f "$CPIO_TEST"
VFS_TEST="$BUILD/vfs-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/tests/vfs_test.cpp" \
  -o "$VFS_TEST"
"$VFS_TEST"
rm -f "$VFS_TEST"
VFS_FD_TEST="$BUILD/vfs-fd-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/core/vfs_fd.cpp" \
  "$ROOT/kernel/tests/vfs_fd_test.cpp" -o "$VFS_FD_TEST"
"$VFS_FD_TEST"
rm -f "$VFS_FD_TEST"
PROCESS_TEST="$BUILD/process-elf-admission-test"
"$HOST_CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/elf64.cpp" "$ROOT/kernel/core/process.cpp" \
  "$ROOT/kernel/tests/process_elf_admission_test.cpp" -o "$PROCESS_TEST"
"$PROCESS_TEST"
rm -f "$PROCESS_TEST"
python3 "$ROOT/tools/isa/generate_registry.py"
CXX="${CXX:-g++}"; NASM="${NASM:-nasm}"; LD="${LD:-ld}"
CXXFLAGS=(-ffreestanding -fno-builtin -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -I"$ROOT/kernel/include")
rm -f "$BUILD"/*.o "$BUILD/koronos.elf"

sources=(koronos elf64 module relocate arch_init runtime runtime_loop scheduler process process_loader frame_allocator address_space target_launch thread sync timer apc dpc hardware nbit firmware device multiboot_modules cpio vfs vfs_fd parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model)
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
  required_symbols=(koronos_idle_loop koronos_user_timeout_arm koronos_user_timeout_disarm koronos_user_timeout_irq koronos_user_timeout_abort koronos_frame_allocator_init koronos_frame_alloc koronos_frame_alloc_contiguous koronos_frame_free koronos_frame_free_contiguous koronos_frame_free_count koronos_address_space_init koronos_address_space_ready koronos_address_space_self_test koronos_address_space_loader_ops koronos_address_space_root koronos_address_space_validate_user_range koronos_address_space_count koronos_user_entry_init koronos_arch_enter_user koronos_syscall_entry koronos_syscall_user_dispatch koronos_launch_selected_userspace koronos_target_note_user_write koronos_target_userspace_ready koronos_target_note_user_syscall koronos_target_validate_syscall_context koronos_target_active_pid koronos_target_log koronos_vfs_open_user koronos_vfs_read_user koronos_vfs_write_user koronos_vfs_seek_user koronos_vfs_close_user koronos_vfs_stat_user koronos_vfs_create_user koronos_vfs_unlink_user koronos_vfs_truncate_user koronos_vfs_chmod_user koronos_vfs_chown_user koronos_vfs_close_process chimera_cpio_find chimera_vfs_init chimera_vfs_create chimera_vfs_stat_path chimera_vfs_read chimera_vfs_write chimera_vfs_truncate chimera_vfs_chmod chimera_vfs_chown chimera_vfs_unlink chimera_vfs_fd_init chimera_vfs_open chimera_vfs_fd_read chimera_vfs_fd_write chimera_vfs_fd_seek chimera_vfs_close chimera_vfs_close_process chimera_multiboot_scan chimera_thread_create chimera_wait_one chimera_timer_tick chimera_apc_deliver chimera_dpc_run chimera_hardware_probe chimera_nbit_init chimera_firmware_probe chimera_hardware_enumerate_devices chimera_driver_probe_all chimera_mk_init chimera_mk_syscall chimera_process_init chimera_process_admit_elf chimera_service_validate chimera_service_resolve chimera_service_set_state chimera_service_get_state chimera_service_start_all chimera_service_stop_all chimera_platform_probe chimera_platform_get_snapshot chimera_object_model_version chimera_object_model_refcount_enabled chimera_sched_run_parallel chimera_compat_init chimera_compat_probe chimera_compat_recognize_syscall chimera_compat_recognize_interrupt chimera_interrupt_init chimera_interrupt_dispatch chimera_syscall_init chimera_syscall_dispatch chimera_isa_init chimera_isa_count chimera_isa_find chimera_isa_find_opcode chimera_ai_model_init chimera_ai_event_count chimera_ai_record_event chimera_ai_provider memset memcpy memmove)
  for symbol in "${required_symbols[@]}"; do
    nm -a --defined-only "$BUILD/koronos.elf" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' || {
      echo "ERROR: $symbol is not linked" >&2; nm -a "$BUILD/koronos.elf" 2>/dev/null | awk -v sym="$symbol" '$NF == sym || index($0,sym)' >&2 || true; exit 1;
    }
  done
fi

grep -aF '[INST] Installer runtime initialization' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: installer bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[SCH ] Bootstrap tasks submitted' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: scheduler bootstrap is missing from Koronos ELF" >&2; exit 1; }
grep -aF '[KORE] Starting initialized kernel services with dependency and health checks' "$BUILD/koronos.elf" >/dev/null || { echo "ERROR: Kore service startup/health-check path is missing from Koronos ELF" >&2; exit 1; }
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
printf 'N-bit artifacts: %s/nbit\n' "$BUILD"