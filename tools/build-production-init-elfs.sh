#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/kernel/userspace/native_init.c"
LD_SCRIPT="$ROOT/kernel/userspace/native_init.ld"
OUT="$ROOT/build/production-init"
STAGE="${CHIMERA_INIT_ELF_STAGE:-$ROOT/boot/iso/dist/iso}"
CC="${CC:-gcc}"
LD="${LD:-ld}"
mkdir -p "$OUT"
test -s "$SRC" && test -s "$LD_SCRIPT"
build_one() {
  local target="$1" name="$2" out="$3"
  local target_id
  case "$target" in live) target_id=1 ;; installer) target_id=2 ;; recovery) target_id=3 ;; *) echo "ERROR: unsupported native init target: $target" >&2; return 2 ;; esac
  local obj="$OUT/user-init-$target.o"
  "$CC" -std=c11 -ffreestanding -fno-builtin -fno-stack-protector -fno-pic -fno-pie -mcmodel=large -mno-red-zone -mno-sse -mno-mmx -nostdlib -Wall -Wextra -Werror -DCHIMERA_INIT_TARGET_ID="$target_id" -DCHIMERA_INIT_TARGET_NAME=\"${name}\" -c "$SRC" -o "$obj"
  "$LD" -nostdlib -z max-page-size=0x1000 -T "$LD_SCRIPT" -o "$OUT/user-init-$target.elf" "$obj"
  test -s "$OUT/user-init-$target.elf"
  readelf -h "$OUT/user-init-$target.elf" | grep -q 'Advanced Micro Devices X86-64'
  readelf -l "$OUT/user-init-$target.elf" | grep -q 'LOAD'
  python3 "$ROOT/tools/validate-native-init-elf.py" --target "$target" "$OUT/user-init-$target.elf"
  mkdir -p "$(dirname "$STAGE/$out")"
  install -m 0644 "$OUT/user-init-$target.elf" "$STAGE/$out"
  printf 'Built fail-closed native init bootstrap: target=%s path=%s\n' "$target" "$STAGE/$out"
}
build_one live live boot/live/user-init-live.elf
build_one installer installer boot/installer/user-init-installer.elf
build_one recovery recovery boot/recovery/user-init-recovery.elf
sha256sum "$STAGE/boot/live/user-init-live.elf" "$STAGE/boot/installer/user-init-installer.elf" "$STAGE/boot/recovery/user-init-recovery.elf" > "$OUT/SHA256SUMS"
