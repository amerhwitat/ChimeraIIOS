#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 <live-iso> <evidence-directory> [live|installer|koronos|recovery]" >&2
  exit 2
fi
ISO="$(realpath "$1")"
OUT="$2"
TARGET=live
if [[ $# -eq 3 ]]; then TARGET="$3"; fi
case "$TARGET" in live|installer|koronos|recovery) ;; *) echo "unsupported target: $TARGET" >&2; exit 2 ;; esac
mkdir -p "$OUT"
test -s "$ISO"
command -v qemu-system-x86_64 >/dev/null
command -v socat >/dev/null
command -v tesseract >/dev/null
sha256sum "$ISO" | tee "$OUT/iso.sha256"
qemu-system-x86_64 --version | head -n1 | tee "$OUT/qemu-version.txt"
work="$(mktemp -d)"
monitor="$work/monitor.sock"
serial="$OUT/serial.log"
qemu_log="$OUT/qemu-monitor.log"
pid=""
cleanup() {
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    printf 'quit\n' | socat - "UNIX-CONNECT:$monitor" >/dev/null 2>&1 || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT
qemu-system-x86_64 \
  -machine pc,accel=tcg -cpu max -m 4096 -smp 2 -vga std -display none \
  -serial "file:$serial" -monitor "unix:$monitor,server,nowait" \
  -netdev user,id=net0 -device e1000,netdev=net0 -boot order=d -no-reboot \
  -cdrom "$ISO" >"$qemu_log" 2>&1 &
pid=$!
for attempt in $(seq 1 100); do
  [[ -S "$monitor" ]] && break
  kill -0 "$pid" 2>/dev/null || { cat "$qemu_log" >&2; exit 1; }
  sleep 0.2
done
[[ -S "$monitor" ]] || { echo "QEMU monitor socket did not appear" >&2; exit 1; }

# GRUB order: Live, Installer, Koronos, Recovery.
if [[ "$TARGET" != live ]]; then
  case "$TARGET" in
    installer) downs=1 ;;
    koronos) downs=2 ;;
    recovery) downs=3 ;;
  esac
  sleep 3
  {
    for ((i=0; i<downs; i++)); do printf 'sendkey down\n'; sleep 0.1; done
    printf 'sendkey ret\n'
  } | socat - "UNIX-CONNECT:$monitor" >>"$qemu_log" 2>&1
fi

case "$TARGET" in
  live) match='Aurora|Application' ;;
  installer) match='INSTALLER NOT CONFIGURED|No disk changes were made' ;;
  koronos) match='Koronos kernel not bundled|Linux-kernel live edition' ;;
  recovery) match='RESCUE SHELL|No disk is modified' ;;
esac
target_seen=0
if [[ "$TARGET" != koronos ]]; then sleep 25; fi
for attempt in $(seq 1 18); do
  sleep 10
  kill -0 "$pid" 2>/dev/null || { cat "$qemu_log" >&2; exit 1; }
  ppm="$OUT/$TARGET-attempt-$attempt.ppm"
  png="$OUT/$TARGET-attempt-$attempt.png"
  printf 'screendump %s\n' "$ppm" | socat - "UNIX-CONNECT:$monitor" >>"$qemu_log" 2>&1 || true
  if [[ ! -s "$ppm" ]]; then continue; fi
  convert "$ppm" -strip "$png"
  identify "$png" >>"$OUT/screenshot-metadata.txt"
  tesseract "$png" "$OUT/$TARGET-attempt-$attempt" 2>/dev/null || true
  ocr="$OUT/$TARGET-attempt-$attempt.txt"
  if [[ -s "$ocr" ]] && grep -Eiq "$match" "$ocr"; then
    cp "$png" "$OUT/$TARGET-boot.png"
    cp "$ocr" "$OUT/$TARGET-boot-ocr.txt"
    target_seen=1
    break
  fi
done
if [[ "$target_seen" -ne 1 ]]; then
  echo "QEMU did not show expected $TARGET target evidence within 180 seconds." >&2
  [[ -f "$OUT/screenshot-metadata.txt" ]] && cat "$OUT/screenshot-metadata.txt" >&2
  for f in "$OUT"/*.txt; do [[ -f "$f" ]] && { echo "---- $f"; cat "$f"; }; done
  exit 1
fi
read -r width height < <(identify -format '%w %h' "$OUT/$TARGET-boot.png")
[[ "$width" -ge 640 && "$height" -ge 480 ]] || {
  echo "QEMU framebuffer unexpectedly small: $width x $height" >&2
  exit 1
}
colors="$(convert "$OUT/$TARGET-boot.png" -colors 64 -format '%k' info:)"
[[ "$colors" -ge 16 ]] || {
  echo "QEMU framebuffer is effectively blank ($colors colors)" >&2
  exit 1
}
cat >"$OUT/RESULT.txt" <<EOF
QEMU $TARGET boot: PASS
ISO: $ISO
Framebuffer: $width x $height
Distinct colors (quantized to 64): $colors
Target OCR evidence: $(tr '\n' ' ' <"$OUT/$TARGET-boot-ocr.txt")
Native Koronos ELF boot: only certified when a real compatible ELF is supplied.
Physical-machine boot: NOT TESTED
EOF
cat "$OUT/RESULT.txt"
