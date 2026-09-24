#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_BOOT_ARTIFACT_DIR:-$ROOT/build/boot-artifacts}"
rm -rf "$OUT"
mkdir -p "$OUT/spitfire" "$OUT/jasper" "$OUT/koronos" "$OUT/grub" "$OUT/all-elf" "$OUT/all-bin" "$OUT/manifests"
KORONOS="$ROOT/build/koronos/x86_64/koronos.elf"
test -s "$KORONOS" || "$ROOT/kernel/build-koronos.sh"
test -s "$KORONOS"
"$ROOT/boot/spitfire/build-spitfire.sh" "$OUT/spitfire" "$KORONOS"
command -v nasm >/dev/null || { echo "nasm required" >&2; exit 2; }
command -v g++ >/dev/null || { echo "g++ required" >&2; exit 2; }
command -v ld >/dev/null || { echo "ld required" >&2; exit 2; }
JASPER_BUILD="$ROOT/build/jasper/x86_64"
mkdir -p "$JASPER_BUILD"
g++ -ffreestanding -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -I"$ROOT/kernel/include" -c "$ROOT/boot/jasper/jasper_main.cpp" -o "$JASPER_BUILD/jasper_main.o"
nasm -f elf64 "$ROOT/boot/jasper/jasper_entry.asm" -o "$JASPER_BUILD/jasper_entry.o"
ld -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/boot/jasper/jasper.ld" "$JASPER_BUILD/jasper_entry.o" "$JASPER_BUILD/jasper_main.o" -o "$JASPER_BUILD/jasper.elf"
cp "$JASPER_BUILD/jasper.elf" "$OUT/jasper/jasper.elf"
cp "$KORONOS" "$OUT/koronos/koronos.elf"
if command -v grub-mkimage >/dev/null 2>&1; then
  MODDIR=""
  for d in /usr/lib/grub/i386-pc /usr/lib/grub/i386-pc-eltorito; do [[ -d "$d" ]] && { MODDIR="$d"; break; }; done
  if [[ -n "$MODDIR" ]]; then
    grub-mkimage -O i386-pc-eltorito -d "$MODDIR" -p /boot/grub -c "$ROOT/boot/iso/grub.cfg" -o "$OUT/grub/grub-core.img" biosdisk iso9660 normal configfile search search_fs_file multiboot2 png gfxterm all_video reboot halt
  fi
fi
find "$ROOT/build" -type f \( -name "*.elf" -o -name "*.bin" -o -name "*.efi" -o -name "*.img" \) -not -path "$ROOT/build/iso/*" -not -path "$ROOT/build/boot-artifacts/*" -print0 2>/dev/null | while IFS= read -r -d "" f; do
  base="$(basename "$f")"
  case "$f" in *.elf) cp -f "$f" "$OUT/all-elf/$base";; *) cp -f "$f" "$OUT/all-bin/$base";; esac
done
cp -f "$OUT/spitfire"/* "$OUT/all-bin/" 2>/dev/null || true
cp -f "$OUT/jasper/jasper.elf" "$OUT/all-elf/"
cp -f "$OUT/koronos/koronos.elf" "$OUT/all-elf/"
[[ -f "$OUT/grub/grub-core.img" ]] && cp -f "$OUT/grub/grub-core.img" "$OUT/all-bin/" || true
sha256sum "$OUT"/all-elf/* "$OUT"/all-bin/* > "$OUT/SHA256SUMS" 2>/dev/null || true
cat > "$OUT/manifests/boot-execution-order.json" <<EOF
{
  "schema": "CHM-BOOT-EXECUTION-3",
  "native_execution_order": [
    {"sequence":1,"id":"spitfire","role":"BIOS/MBR native bootstrap"},
    {"sequence":2,"id":"jasper","role":"boot policy and stage selection"},
    {"sequence":3,"id":"grub","role":"filesystem-aware final boot manager and Multiboot2 loader"},
    {"sequence":4,"id":"koronos","role":"Chimera II OS kernel"}
  ],
  "iso_fallback": {"sequence":["firmware","grub","jasper-menu","koronos"],"reason":"El Torito firmware selects the ISO boot image; GRUB remains the standards-compatible ISO fallback."},
  "kernel_protocol":"Multiboot2",
  "elf_policy":"Every generated runtime/boot ELF is staged and checksummed; relocatable .o files remain build inputs and are not treated as executable boot payloads."
}
EOF
cp "$OUT/manifests/boot-execution-order.json" "$OUT/"
echo "Boot artifacts generated: $OUT"
