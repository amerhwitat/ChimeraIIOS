#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "usage: $0 <live-iso> <evidence-directory>" >&2
  exit 2
fi
ISO="$(realpath "$1")"
OUT="$2"
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
desktop_seen=0
for attempt in $(seq 1 18); do
  sleep 10
  kill -0 "$pid" 2>/dev/null || { cat "$qemu_log" >&2; exit 1; }
  ppm="$OUT/desktop-attempt-$attempt.ppm"
  png="$OUT/desktop-attempt-$attempt.png"
  printf 'screendump %s\n' "$ppm" | socat - "UNIX-CONNECT:$monitor" >>"$qemu_log" 2>&1 || true
  if [[ ! -s "$ppm" ]]; then continue; fi
  convert "$ppm" -strip "$png"
  identify "$png" >>"$OUT/screenshot-metadata.txt"
  tesseract "$png" "$OUT/desktop-attempt-$attempt" 2>/dev/null || true
  ocr="$OUT/desktop-attempt-$attempt.txt"
  if [[ -s "$ocr" ]] && grep -Eiq 'Aurora|Desktop|Chimera|Octavian|Application' "$ocr"; then
    cp "$png" "$OUT/desktop-boot.png"
    cp "$ocr" "$OUT/desktop-boot-ocr.txt"
    desktop_seen=1
    break
  fi
done
if [[ "$desktop_seen" -ne 1 ]]; then
  echo "QEMU did not show OCR-verifiable Aurora desktop content within 180 seconds." >&2
  [[ -f "$OUT/screenshot-metadata.txt" ]] && cat "$OUT/screenshot-metadata.txt" >&2
  for f in "$OUT"/*.txt; do [[ -f "$f" ]] && { echo "---- $f"; cat "$f"; }; done
  exit 1
fi
read -r width height < <(identify -format '%w %h' "$OUT/desktop-boot.png")
[[ "$width" -ge 640 && "$height" -ge 480 ]] || {
  echo "QEMU framebuffer unexpectedly small: \${width}x\${height}" >&2
  exit 1
}
colors="$(convert "$OUT/desktop-boot.png" -colors 64 -format '%k' info:)"
[[ "$colors" -ge 16 ]] || {
  echo "QEMU framebuffer is effectively blank ($colors colors)" >&2
  exit 1
}
cat >"$OUT/RESULT.txt" <<EOF
QEMU live boot: PASS
ISO: $ISO
Framebuffer: \${width}x\${height}
Distinct colors (quantized to 64): $colors
Desktop OCR evidence: $(tr '\n' ' ' <"$OUT/desktop-boot-ocr.txt")
Physical-machine boot: NOT TESTED
Native Koronos kernel: NOT TESTED; this is a Linux-kernel live edition.
EOF
cat "$OUT/RESULT.txt"
