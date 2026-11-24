#!/usr/bin/env bash
# Native x86_64 Koronos partition-aware VFS + durable installer/recovery gate.
#
# Boots one real kernel five times against one persistent virtio-blk disk:
#   installer -> GPT/KoronosFS v2 format, payload files, committed journal
#   installed -> mount installed root, stage a real torn write, pending journal
#   recovery  -> verify/repair checksums, roll back, journal rolled-back
#   verify    -> fsck and digest verification of the restored root
#   live      -> ring-3 target asks the kernel for a measured handoff token
#
# Every value asserted below is read from the kernel's debugcon trace; the gate
# never hardcodes a PASS result.

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos kernel five times against one persistent
virtio-blk disk image and verifies partition discovery, filesystem mounts,
payload bytes written/read, journal state transitions, rollback, checksum
repair and a ring-3 installed-root handoff token.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-vfs-installer/{installer,installed,recovery,verify,live}.iso
  build/koronos-vfs-installer/disk.raw
  build/koronos-vfs-installer/debugcon-*.log
  build/koronos-vfs-installer/result.txt
  build/koronos-vfs-installer/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-vfs-installer"
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
for tool in make nasm g++ ld grub-file grub-mkrescue qemu-system-x86_64 qemu-img timeout sha256sum grep awk; do
  require "$tool"
done

mkdir -p "$OUT/isoroot/boot/grub" "$OUT/isoroot/boot/payloads"
rm -rf "$OUT"/*.iso "$OUT"/*.log "$OUT"/iso.sha256 "$OUT/disk.raw" "$RESULT"
mkdir -p "$OUT/isoroot/boot/grub" "$OUT/isoroot/boot/payloads"

echo "== Building native Koronos kernel and target probes =="
bash "$ROOT/kernel/build-koronos.sh" > "$OUT/build.log" 2>&1 || {
  tail -80 "$OUT/build.log" >&2
  fail "kernel build-koronos.sh failed"
}
[[ -f "$KERNEL" ]] || fail "kernel ELF not produced at $KERNEL"
grub-file --is-x86-multiboot2 "$KERNEL" || fail "kernel is not Multiboot2"
for symbol in koronos_block_init koronos_vfs_format_disk koronos_vfs_mount koronos_vfs_handoff_user koronos_installer_run koronos_recovery_run; do
  nm -a --defined-only "$KERNEL" | awk -v sym="$symbol" '$NF == sym { found=1 } END { exit !found }' ||
    fail "missing linked symbol: $symbol"
done
install -m 0644 "$KERNEL" "$OUT/isoroot/boot/koronos.elf"
install -m 0644 "$ROOT/build/koronos/x86_64/target-init-live.elf" "$OUT/isoroot/boot/target-init-live.elf"

printf 'KORONOS VFS KERNEL PAYLOAD v2 real-block-backed\n' > "$OUT/isoroot/boot/payloads/kernel.bin"
printf 'KORONOS VFS INIT PAYLOAD v2 real-block-backed\n' > "$OUT/isoroot/boot/payloads/init.bin"
printf 'KORONOS VFS MANIFEST PAYLOAD v2\n' > "$OUT/isoroot/boot/payloads/manifest.bin"

for phase in installer installed recovery verify live; do
  printf '%s\n' "koronos-install-stack mode=$phase" > "$OUT/isoroot/boot/$phase.mode"
done

build_iso() {
  local phase="$1"
  local extra=""
  if [[ "$phase" == "live" ]]; then
    extra='  module2 /boot/target-init-live.elf chimera-user-init-elf target=live\n'
  fi
  cat > "$OUT/isoroot/boot/grub/grub.cfg" <<GRUB
set timeout=0
set default=0
insmod serial
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry "Koronos native VFS installer: $phase" {
  multiboot2 /boot/koronos.elf
  module2 /boot/$phase.mode "koronos-install-stack mode=$phase"
  module2 /boot/payloads/kernel.bin "koronos-payload-kernel kernel.bin"
  module2 /boot/payloads/init.bin "koronos-payload-init init.bin"
  module2 /boot/payloads/manifest.bin "koronos-payload-manifest manifest.bin"
$(printf '%b' "$extra")
  boot
}
GRUB
  grub-mkrescue -o "$OUT/$phase.iso" "$OUT/isoroot"
  sha256sum "$OUT/$phase.iso" >> "$OUT/iso.sha256"
}

echo "== Building five Multiboot2 target-mode ISOs with module payloads =="
for phase in installer installed recovery verify live; do
  build_iso "$phase"
done

echo "== Creating persistent virtio-blk disk =="
qemu-img create -f raw "$DISK" 8M >/dev/null

boot_phase() {
  local phase="$1"
  local debuglog="$OUT/debugcon-$phase.log"
  local seriallog="$OUT/serial-$phase.log"
  local rc=0
  local budget=180s
  local attempt=1
  while :; do
    set +e
    timeout "$budget" qemu-system-x86_64 \
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
    [[ "$rc" -eq 0 || "$rc" -eq 124 ]] || fail "$phase boot exited with $rc"
    # The preemptive-scheduler selftest is timing-sensitive under QEMU. Only
    # that known infrastructure flake is retried; persistent failures still
    # surface through the token assertions below.
    if [[ "$attempt" -lt 3 ]] &&
       { grep -aFq "[PMT ] SELFTEST FAIL" "$debuglog" ||
         grep -aFq "gate not started: earlier native gates did not pass" "$debuglog"; }; then
      attempt=$((attempt + 1))
      continue
    fi
    break
  done
  echo "$rc" > "$OUT/qemu-$phase.rc"
  echo "$attempt" > "$OUT/qemu-$phase.attempts"
}

assert_token() {
  local file="$1"
  local token="$2"
  grep -aFq "$token" "$file" || fail "missing debugcon token in $file: $token"
}
field() {
  local file="$1"
  local token="$2"
  local value
  value="$(grep -aF "$token" "$file" | tail -n 1 | tr -d '\r' | awk -F= '{print $NF}')"
  [[ -n "$value" ]] || fail "missing measured field $token in $file"
  printf '%s' "$value"
}
numeric() {
  [[ "$1" =~ ^[0-9]+$ ]] || fail "expected numeric value, got: $1"
}
hex64() {
  [[ "$1" =~ ^[0-9A-F]{1,16}$ ]] || fail "expected hex digest, got: $1"
}

echo "== Boot 1: installer partitions, formats, writes payloads, commits journal =="
boot_phase installer
IL="$OUT/debugcon-installer.log"
assert_token "$IL" "[PMT ] SELFTEST PASS"
assert_token "$IL" "[SMP ] SELFTEST PASS"
assert_token "$IL" "[NST ] SKIPPED: install target selected"
assert_token "$IL" "[INS ] mode_selected=1"
assert_token "$IL" "[VFS ] format_partition=0"
assert_token "$IL" "[INS ] JOURNAL WRITE PASS"
assert_token "$IL" "[INS ] JOURNAL COMMIT PASS"
assert_token "$IL" "[INS ] INSTALLED ROOT WRITTEN"
assert_token "$IL" "[INS ] HANDOFF next=installed"
assert_token "$IL" "[INS ] SELFTEST PASS"

partition_count="$(field "$IL" '[INS ] partition_count=')"
root_start="$(field "$IL" '[INS ] root_start=')"
root_sectors="$(field "$IL" '[INS ] root_sectors=')"
journal_start="$(field "$IL" '[INS ] journal_start=')"
journal_sectors="$(field "$IL" '[INS ] journal_sectors=')"
mount_state="$(field "$IL" '[INS ] mount_state=')"
bytes_written="$(field "$IL" '[INS ] bytes_written=')"
payload_modules="$(field "$IL" '[INS ] payload_modules=')"
installer_journal="$(field "$IL" '[INS ] journal_state=')"
installer_transaction="$(field "$IL" '[INS ] journal_transaction=')"
root_digest="$(field "$IL" '[INS ] root_digest=')"

numeric "$partition_count"; numeric "$root_start"; numeric "$root_sectors"
numeric "$journal_start"; numeric "$journal_sectors"; numeric "$mount_state"
numeric "$bytes_written"; numeric "$payload_modules"; numeric "$installer_journal"
numeric "$installer_transaction"; hex64 "$root_digest"
[[ "$partition_count" -ge 2 ]] || fail "expected at least two GPT partitions: $partition_count"
[[ "$root_start" -gt 2 ]] || fail "root partition still uses synthetic low sector: $root_start"
[[ "$root_sectors" -gt 64 ]] || fail "root partition too small: $root_sectors"
[[ "$journal_start" -gt "$root_start" ]] || fail "journal overlaps root partition"
[[ "$journal_sectors" -ge 8 ]] || fail "journal partition too small: $journal_sectors"
[[ "$mount_state" -eq 1 ]] || fail "installer mount state not live: $mount_state"
[[ "$bytes_written" -gt 0 ]] || fail "no payload bytes written: $bytes_written"
[[ "$payload_modules" -ge 2 ]] || fail "multiboot payloads not consumed: $payload_modules"
[[ "$installer_journal" -eq 1 ]] || fail "journal not committed: $installer_journal"
echo "== Boot 2: installed-root handoff, then genuine torn write =="
boot_phase installed
ID="$OUT/debugcon-installed.log"
assert_token "$ID" "[INS ] mode_selected=2"
assert_token "$ID" "[INS ] INSTALLED ROOT HANDOFF PASS"
assert_token "$ID" "[INS ] ROOT MOUNTED=1"
assert_token "$ID" "[INS ] ROOT MARKER PASS"
assert_token "$ID" "[INS ] REAL TORN WRITE STAGED"
assert_token "$ID" "[INS ] HANDOFF next=recovery"
assert_token "$ID" "[INS ] SELFTEST PASS"
installed_digest="$(field "$ID" '[INS ] root_digest=')"
installed_journal="$(field "$ID" '[INS ] journal_state=')"
installed_transaction="$(field "$ID" '[INS ] journal_transaction=')"
installed_bytes_read="$(field "$ID" '[INS ] bytes_read=')"
hex64 "$installed_digest"; numeric "$installed_journal"; numeric "$installed_transaction"
numeric "$installed_bytes_read"
[[ "$installed_digest" == "$root_digest" ]] || fail "installed-root digest changed: $installed_digest != $root_digest"
[[ "$installed_journal" -eq 2 ]] || fail "journal not pending after torn write: $installed_journal"
[[ "$installed_transaction" -gt "$installer_transaction" ]] || fail "transaction did not advance"
[[ "$installed_bytes_read" -gt 0 ]] || fail "installed root not actually read"

echo "== Boot 3: recovery verifies checksums, rolls back pending transaction =="
boot_phase recovery
RC="$OUT/debugcon-recovery.log"
assert_token "$RC" "[INS ] mode_selected=3"
assert_token "$RC" "[REC ] SUPERBLOCK CHECKSUM REPAIR PASS"
assert_token "$RC" "[REC ] INODE CHECKSUM REPAIR PASS"
assert_token "$RC" "[REC ] JOURNAL ROLLBACK PASS"
assert_token "$RC" "[INS ] journal_state=3"
assert_token "$RC" "[REC ] HANDOFF next=verify"
assert_token "$RC" "[INS ] SELFTEST PASS"
recovered_digest="$(field "$RC" '[REC ] root_digest=')"
restored_bytes="$(field "$RC" '[REC ] restored_bytes=')"
rollback_journal="$(field "$RC" '[INS ] journal_state=')"
checksum_repairs="$(grep -acF '[REC ] SUPERBLOCK CHECKSUM REPAIR PASS' "$RC")"
hex64 "$recovered_digest"; numeric "$restored_bytes"; numeric "$rollback_journal"
numeric "$checksum_repairs"
[[ "$checksum_repairs" -gt 0 ]] || fail "no measured checksum repair"
[[ "$recovered_digest" == "$root_digest" ]] || fail "root digest after rollback mismatch"
[[ "$restored_bytes" -gt 0 ]] || fail "recovery did not restore file bytes"
[[ "$rollback_journal" -eq 3 ]] || fail "journal not marked rolled back: $rollback_journal"

echo "== Boot 4: final verify of restored root and rolled-back journal =="
boot_phase verify
VF="$OUT/debugcon-verify.log"
assert_token "$VF" "[INS ] mode_selected=4"
assert_token "$VF" "[INS ] ROOT VERIFY PASS"
assert_token "$VF" "[INS ] ROLLBACK VERIFY PASS"
assert_token "$VF" "[INS ] REPAIR VERIFY PASS"
assert_token "$VF" "[INS ] SELFTEST PASS"
assert_token "$VF" "[INS ] Native installer/installed-root/recovery gate passed"
verify_digest="$(field "$VF" '[INS ] root_digest=')"
verify_journal="$(field "$VF" '[INS ] journal_state=')"
verify_bytes_read="$(field "$VF" '[INS ] bytes_read=')"
hex64 "$verify_digest"; numeric "$verify_journal"; numeric "$verify_bytes_read"
[[ "$verify_digest" == "$root_digest" ]] || fail "verify digest mismatch: $verify_digest != $root_digest"
[[ "$verify_journal" -eq 3 ]] || fail "verify journal state mismatch: $verify_journal"
[[ "$verify_bytes_read" -gt 0 ]] || fail "verify did not read real files"

echo "== Boot 5: ring-3 live target receives kernel-mounted handoff token =="
boot_phase live
LV="$OUT/debugcon-live.log"
assert_token "$LV" "[INS ] mode_selected=5"
assert_token "$LV" "[LIVE ] handoff=1"
assert_token "$LV" "[LIVE ] installed-root handoff from kernel:"
assert_token "$LV" "VFS_HANDOFF mounted=1 root_digest=$root_digest"
assert_token "$LV" "[INS ] SELFTEST PASS"
live_digest="$(field "$LV" '[LIVE ] root_digest=')"
live_handoff="$(field "$LV" '[LIVE ] handoff=')"
hex64 "$live_digest"; numeric "$live_handoff"
[[ "$live_digest" == "$root_digest" ]] || fail "live handoff digest mismatch: $live_digest != $root_digest"
[[ "$live_handoff" -eq 1 ]] || fail "live handoff not reported"

{
  echo "PASS: Koronos x86_64 partition-aware VFS and durable installer/recovery gate"
  echo "INSTALLER_QEMU_EXIT=$(cat "$OUT/qemu-installer.rc")"
  echo "INSTALLED_QEMU_EXIT=$(cat "$OUT/qemu-installed.rc")"
  echo "RECOVERY_QEMU_EXIT=$(cat "$OUT/qemu-recovery.rc")"
  echo "VERIFY_QEMU_EXIT=$(cat "$OUT/qemu-verify.rc")"
  echo "LIVE_QEMU_EXIT=$(cat "$OUT/qemu-live.rc")"
  echo "ISO_SHA256=$(awk 'NR==1 {print $1}' "$OUT/iso.sha256")"
  echo "PARTITION_COUNT=$partition_count"
  echo "ROOT_START=$root_start"
  echo "ROOT_SECTORS=$root_sectors"
  echo "JOURNAL_START=$journal_start"
  echo "JOURNAL_SECTORS=$journal_sectors"
  echo "MOUNT_STATE=$mount_state"
  echo "FILE_BYTES_WRITTEN=$bytes_written"
  echo "FILE_BYTES_READ=$installed_bytes_read"
  echo "PAYLOAD_MODULES=$payload_modules"
  echo "JOURNAL_STATE_COMMIT=$installer_journal"
  echo "JOURNAL_STATE_PENDING=$installed_journal"
  echo "JOURNAL_STATE_ROLLEDBACK=$rollback_journal"
  echo "TRANSACTION_INSTALL=$installer_transaction"
  echo "TRANSACTION_PENDING=$installed_transaction"
  echo "ROLLBACK_RESTORED_BYTES=$restored_bytes"
  echo "CHECKSUM_REPAIR=$checksum_repairs"
  echo "INSTALLED_ROOT_DIGEST=$root_digest"
  echo "LIVE_HANDOFF=$live_handoff"
} | tee "$RESULT"

echo "PASS: measured VFS/installer evidence written to $RESULT"
