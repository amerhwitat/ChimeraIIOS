#!/usr/bin/env bash
# Native x86_64 Koronos block/VFS/PID 1 gate.
#
# Boots the real kernel with a persistent virtio-blk disk. On the first boot
# the kernel writes a marker through the real block device and resets the
# machine; on the second boot it mounts the block filesystem, reads the marker
# back, and exercises PID 1 child creation/exit/reaping. All preemption and
# AP/SMP evidence must also be present in the final boot trace.
#
# Usage: tools/runtime/check-koronos-native-stack.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel twice against one persistent
virtio-blk disk image and verifies block I/O, mount, reboot persistence, and
PID 1 supervision/reaping.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-native-stack/koronos-native-stack-gate.iso
  build/koronos-native-stack/disk.raw
  build/koronos-native-stack/debugcon-write.log
  build/koronos-native-stack/debugcon-read.log
  build/koronos-native-stack/result.txt
  build/koronos-native-stack/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-native-stack"
ISO="$OUT/koronos-native-stack-gate.iso"
DISK="$OUT/disk.raw"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
WRITE_LOG="$OUT/debugcon-write.log"
READ_LOG="$OUT/debugcon-read.log"
RESULT="$OUT/result.txt"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

for tool in make nasm g++ ld grub-file grub-mkrescue qemu-system-x86_64 qemu-img timeout sha256sum; do
  require "$tool"
done

mkdir -p "$OUT/isoroot/boot/grub"
rm -f "$ISO" "$DISK" "$WRITE_LOG" "$READ_LOG" "$RESULT" "$OUT/iso.sha256" \
      "$OUT/serial-write.log" "$OUT/serial-read.log"

echo "== Building native Koronos kernel =="
make -C "$ROOT/kernel" -j2
[[ -f "$KERNEL" ]] || fail "kernel ELF not produced at $KERNEL"
grub-file --is-x86-multiboot2 "$KERNEL" || fail "kernel is not Multiboot2"

install -m 0644 "$KERNEL" "$OUT/isoroot/boot/koronos.elf"
cat > "$OUT/isoroot/boot/grub/grub.cfg" <<'GRUB'
set timeout=0
set default=0
insmod serial
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry "Koronos native block/VFS/PID1 gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 native-stack test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot"
sha256sum "$ISO" | tee "$OUT/iso.sha256"

echo "== Creating persistent virtio-blk disk =="
qemu-img create -f raw "$DISK" 8M >/dev/null

qemu_boot() {
  local debuglog="$1"
  local seriallog="$2"
  timeout 180s qemu-system-x86_64 \
    -machine pc \
    -cpu max \
    -smp 2 \
    -m 256M \
    -cdrom "$ISO" \
    -boot d \
    -drive "file=$DISK,if=virtio,format=raw" \
    -serial "file:$seriallog" \
    -debugcon "file:$debuglog" \
    -global isa-debugcon.iobase=0xe9 \
    -display none \
    -no-reboot >"$OUT/qemu.stdout" 2>"$OUT/qemu.stderr"
}

echo "== Boot 1: writing marker through virtio-blk, then reset =="
set +e
qemu_boot "$WRITE_LOG" "$OUT/serial-write.log"
write_rc=$?
set -e
[[ "$write_rc" -eq 0 || "$write_rc" -eq 124 ]] || fail "first QEMU boot exited with $write_rc"

assert_token() {
  local file="$1"
  local token="$2"
  grep -aFq "$token" "$file" || fail "missing debugcon token in $file: $token"
}
field() {
  local file="$1"
  local token="$2"
  grep -aF "$token" "$file" | tail -n 1 | tr -d '\r' | awk -F= '{print $2}'
}

assert_token "$WRITE_LOG" "[NST ] PERSIST WRITE PASS"
assert_token "$WRITE_LOG" "[NST ] REBOOTING FOR PERSISTENCE CHECK"

echo "== Boot 2: mounting filesystem, verifying persistence and PID 1 =="
set +e
qemu_boot "$READ_LOG" "$OUT/serial-read.log"
read_rc=$?
set -e
[[ "$read_rc" -eq 0 || "$read_rc" -eq 124 ]] || fail "second QEMU boot exited with $read_rc"

# Ordered native gates: earlier evidence must precede the final gate.
assert_token "$READ_LOG" "[PMT ] SELFTEST PASS"
assert_token "$READ_LOG" "[SMP ] SELFTEST PASS"
assert_token "$READ_LOG" "[NST ] PERSIST READ PASS"
assert_token "$READ_LOG" "[NST ] mounted=1"
assert_token "$READ_LOG" "[NST ] self-tests passed"
assert_token "$READ_LOG" "[NST ] SELFTEST PASS"
assert_token "$READ_LOG" "[NST ] Native block/VFS/PID1 gate passed"

sectors="$(field "$READ_LOG" '[NST ] block_sectors=')"
mounted="$(field "$READ_LOG" '[NST ] mounted=')"
child_progress="$(field "$READ_LOG" '[NST ] child_progress=')"
child_status="$(field "$READ_LOG" '[NST ] child_exit_status=')"
reaped_pid="$(field "$READ_LOG" '[NST ] reaped_pid=')"
reaped_status="$(field "$READ_LOG" '[NST ] reaped_status=')"
zombies="$(field "$READ_LOG" '[NST ] zombies_after_reap=')"

[[ -n "$sectors" && "$sectors" -gt 1 ]] || fail "virtio-blk capacity not reported: $sectors"
[[ "$mounted" == "1" ]] || fail "filesystem not mounted: $mounted"
[[ "$child_progress" == "1000" ]] || fail "child did not complete work: $child_progress"
[[ "$child_status" == "7" ]] || fail "unexpected child exit status: $child_status"
[[ "$reaped_pid" == "2" ]] || fail "PID 1 did not reap child: $reaped_pid"
[[ "$reaped_status" == "7" ]] || fail "reaped status mismatch: $reaped_status"
[[ "$zombies" == "0" ]] || fail "zombies remain after reap: $zombies"

{
  echo "PASS: Koronos x86_64 native block/VFS/PID1 gate"
  echo "BOOT1_QEMU_EXIT=$write_rc"
  echo "BOOT2_QEMU_EXIT=$read_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "BLOCK_SECTORS=$sectors"
  echo "MOUNTED=$mounted"
  echo "CHILD_PROGRESS=$child_progress"
  echo "CHILD_EXIT_STATUS=$child_status"
  echo "REAPED_PID=$reaped_pid"
  echo "REAPED_STATUS=$reaped_status"
  echo "ZOMBIES_AFTER_REAP=$zombies"
} | tee "$RESULT"

echo "PASS: native block/VFS/PID1 evidence written to $RESULT"
