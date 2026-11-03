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
  -serial "file:$serial" -debugcon "file:$OUT/debugcon.log" -global isa-debugcon.iobase=0xe9 \
  -monitor "unix:$monitor,server,nowait" \
  -netdev user,id=net0 -device e1000,netdev=net0 -boot order=d -no-reboot \
  -cdrom "$ISO" >"$qemu_log" 2>&1 &
pid=$!
for attempt in $(seq 1 100); do
  [[ -S "$monitor" ]] && break
  kill -0 "$pid" 2>/dev/null || { cat "$qemu_log" >&2; exit 1; }
  sleep 0.2
done
[[ -S "$monitor" ]] || { echo "QEMU monitor socket did not appear" >&2; exit 1; }

# First menu is Spit Fire. Its default item hands off to the Jasper/GRUB2
# target menu. Then select the requested Jasper item.
sleep 3
printf 'sendkey ret\n' | socat - "UNIX-CONNECT:$monitor" >>"$qemu_log" 2>&1
sleep 2
if [[ "$TARGET" != live ]]; then
  case "$TARGET" in
    recovery) downs=2 ;;  # Linux Rescue Shell
    installer) downs=3 ;; # Native Installer; must refuse incomplete payloads
    koronos) downs=5 ;;   # Native Koronos diagnostics
  esac
  {
    for ((i=0; i<downs; i++)); do printf 'sendkey down\n'; sleep 0.1; done
    printf 'sendkey ret\n'
  } | socat - "UNIX-CONNECT:$monitor" >>"$qemu_log" 2>&1
fi

case "$TARGET" in
  live) match='Aurora|Application' ;;
  installer) match='Native Koronos Installer runtime incomplete|No Linux fallback is called an installer' ;;
  koronos)
    # Kernel entry emits E (32-bit), L (long mode), B (kernel entry), C (idle loop) to port 0xE9.
    for attempt in $(seq 1 30); do
      sleep 1
      if [[ -s "$OUT/debugcon.log" ]] && grep -q "ELBC" "$OUT/debugcon.log"; then
        cat >"$OUT/RESULT.txt" <<EOF
QEMU native Koronos Multiboot2 boot: PASS
Observed debug-port sequence: $(cat "$OUT/debugcon.log")
Physical-machine boot: NOT TESTED
CPL3 userspace readiness: NOT IMPLIED BY THIS ENTRY MARKER.
EOF
        cat "$OUT/RESULT.txt"
        exit 0
      fi
    done
    echo "Koronos did not emit the complete ELBC entry sequence." >&2
    cat "$OUT/debugcon.log" 2>/dev/null || true
    exit 1
    ;;
  recovery) match='RESCUE SHELL|Recovery shell|No disk is modified' ;;
esac

target_seen=0
if [[ "$TARGET" == installer ]]; then
  initial_wait=1
  poll_attempts=10
  poll_interval=1
else
  initial_wait=25
  poll_attempts=18
  poll_interval=10
fi
sleep "$initial_wait"
for attempt in $(seq 1 "$poll_attempts"); do
  sleep "$poll_interval"
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
  echo "QEMU did not show expected $TARGET target evidence within the target-specific timeout." >&2
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
Installer acceptance here proves fail-closed refusal when the native runtime is incomplete; it does not certify a working native installer.
Recovery acceptance here verifies the separate Linux rescue shell, not native Koronos Recovery.
Physical-machine boot: NOT TESTED
EOF
cat "$OUT/RESULT.txt"
