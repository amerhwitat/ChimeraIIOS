#!/usr/bin/env bash
# Native x86_64 Koronos installer / installed-root / recovery gate.
#
# Boots the real kernel four times against one persistent virtio-blk disk. Each
# boot carries a Multiboot2 module cmdline selecting installer, installed-root,
# recovery, or verify. The gate requires a committed installer journal, a real
# installed-root handoff, an interrupted transaction rollback, actual filesystem
# superblock repair, and a final verify boot.
#
# Usage: tools/runtime/check-koronos-install-recovery.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos kernel four times against one persistent
virtio-blk disk image and verifies installer writes, journal commit, installed
root handoff, rollback of a pending transaction, filesystem repair, and final
verification.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-install-recovery/{installer,installed,recovery,verify}.iso
  build/koronos-install-recovery/disk.raw
  build/koronos-install-recovery/debugcon-*.log
  build/koronos-install-recovery/result.txt
  build/koronos-install-recovery/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-install-recovery"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
DISK="$OUT/disk.raw"
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
rm -rf "$OUT"/*.iso "$OUT"/*.log "$OUT"/iso.sha256 "$OUT/disk.raw" "$RESULT"
mkdir -p "$OUT/isoroot/boot/grub"

echo "== Building native Koronos kernel =="
make -C "$ROOT/kernel" -j2
[[ -f "$KERNEL" ]] || fail "kernel ELF not produced at $KERNEL"
grub-file --is-x86-multiboot2 "$KERNEL" || fail "kernel is not Multiboot2"
install -m 0644 "$KERNEL" "$OUT/isoroot/boot/koronos.elf"
for phase in installer installed recovery verify; do
  printf '%s\n' "koronos-install-stack mode=$phase" > "$OUT/isoroot/boot/$phase.mode"
done

build_iso() {
  local phase="$1"
  cat > "$OUT/isoroot/boot/grub/grub.cfg" <<GRUB
set timeout=0
set default=0
insmod serial
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry "Koronos native install stack: $phase" {
  multiboot2 /boot/koronos.elf
  module2 /boot/$phase.mode "koronos-install-stack mode=$phase"
  boot
}
GRUB
  grub-mkrescue -o "$OUT/$phase.iso" "$OUT/isoroot"
  sha256sum "$OUT/$phase.iso" >> "$OUT/iso.sha256"
}

echo "== Building four Multiboot2 target-mode ISOs =="
build_iso installer
build_iso installed
build_iso recovery
build_iso verify

echo "== Creating persistent virtio-blk disk =="
qemu-img create -f raw "$DISK" 8M >/dev/null

boot_phase() {
  local phase="$1"
  local debuglog="$OUT/debugcon-$phase.log"
  local seriallog="$OUT/serial-$phase.log"
  local rc=0
  set +e
  timeout 180s qemu-system-x86_64 \
    -machine pc \
    -cpu max \
    -smp 2 \
    -m 256M \
    -cdrom "$OUT/$phase.iso" \
    -boot d \
    -drive "file=$DISK,if=virtio,format=raw" \
    -serial "file:$seriallog" \
    -debugcon "file:$debuglog" \
    -global isa-debugcon.iobase=0xe9 \
    -display none \
    -no-reboot >"$OUT/qemu-$phase.stdout" 2>"$OUT/qemu-$phase.stderr"
  rc=$?
  set -e
  echo "$rc" > "$OUT/qemu-$phase.rc"
  [[ "$rc" -eq 0 || "$rc" -eq 124 ]] || fail "$phase boot exited with $rc"
}

assert_token() {
  local file="$1"
  local token="$2"
  grep -aFq "$token" "$file" || fail "missing debugcon token in $file: $token"
}

echo "== Boot 1: installer writes committed journal and installed root =="
boot_phase installer
IL="$OUT/debugcon-installer.log"
assert_token "$IL" "[PMT ] SELFTEST PASS"
assert_token "$IL" "[SMP ] SELFTEST PASS"
assert_token "$IL" "[NST ] SKIPPED: install target selected"
assert_token "$IL" "[INS ] mode_selected=1"
assert_token "$IL" "[INS ] JOURNAL WRITE PASS"
assert_token "$IL" "[INS ] JOURNAL COMMIT PASS"
assert_token "$IL" "[INS ] INSTALLED ROOT WRITTEN"
assert_token "$IL" "[INS ] HANDOFF next=installed"
assert_token "$IL" "[INS ] SELFTEST PASS"
assert_token "$IL" "[INS ] REBOOTING FOR NEXT PHASE"

echo "== Boot 2: installed-root handoff, then interrupted transaction =="
boot_phase installed
ID="$OUT/debugcon-installed.log"
assert_token "$ID" "[PMT ] SELFTEST PASS"
assert_token "$ID" "[SMP ] SELFTEST PASS"
assert_token "$ID" "[INS ] mode_selected=2"
assert_token "$ID" "[INS ] INSTALLED ROOT HANDOFF PASS"
assert_token "$ID" "[INS ] ROOT MOUNTED=1"
assert_token "$ID" "[INS ] ROOT MARKER PASS"
assert_token "$ID" "[INS ] CRASH SIMULATION PASS"
assert_token "$ID" "[INS ] HANDOFF next=recovery"
assert_token "$ID" "[INS ] SELFTEST PASS"
assert_token "$ID" "[INS ] REBOOTING FOR NEXT PHASE"

echo "== Boot 3: recovery rolls back journal and repairs superblock =="
boot_phase recovery
RC="$OUT/debugcon-recovery.log"
assert_token "$RC" "[PMT ] SELFTEST PASS"
assert_token "$RC" "[SMP ] SELFTEST PASS"
assert_token "$RC" "[INS ] mode_selected=3"
assert_token "$RC" "[REC ] JOURNAL ROLLBACK PASS"
assert_token "$RC" "[REC ] SUPERBLOCK REPAIR PASS"
assert_token "$RC" "[REC ] FILESYSTEM REPAIR PASS"
assert_token "$RC" "[REC ] HANDOFF next=verify"
assert_token "$RC" "[INS ] SELFTEST PASS"
assert_token "$RC" "[INS ] REBOOTING FOR NEXT PHASE"

echo "== Boot 4: verify restored root, rollback and repair =="
boot_phase verify
VF="$OUT/debugcon-verify.log"
assert_token "$VF" "[PMT ] SELFTEST PASS"
assert_token "$VF" "[SMP ] SELFTEST PASS"
assert_token "$VF" "[INS ] mode_selected=4"
assert_token "$VF" "[INS ] ROOT VERIFY PASS"
assert_token "$VF" "[INS ] ROLLBACK VERIFY PASS"
assert_token "$VF" "[INS ] REPAIR VERIFY PASS"
assert_token "$VF" "[INS ] SELFTEST PASS"
assert_token "$VF" "[INS ] Native installer/installed-root/recovery gate passed"

{
  echo "PASS: Koronos x86_64 native installer/installed-root/recovery gate"
  echo "INSTALLER_QEMU_EXIT=$(cat "$OUT/qemu-installer.rc")"
  echo "INSTALLED_QEMU_EXIT=$(cat "$OUT/qemu-installed.rc")"
  echo "RECOVERY_QEMU_EXIT=$(cat "$OUT/qemu-recovery.rc")"
  echo "VERIFY_QEMU_EXIT=$(cat "$OUT/qemu-verify.rc")"
  echo "JOURNAL_WRITE=1"
  echo "JOURNAL_COMMIT=1"
  echo "INSTALLED_HANDOFF=1"
  echo "ROLLBACK=1"
  echo "FILESYSTEM_REPAIR=1"
  echo "FINAL_VERIFY=1"
} | tee "$RESULT"

echo "PASS: native installer/recovery evidence written to $RESULT"
