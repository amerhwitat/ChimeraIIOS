#!/usr/bin/env bash
set -euo pipefail

firmware="${FIRMWARE:-bios}"
memory="${MEMORY:-2048}"
cpus="${CPUS:-2}"
display="${QEMU_DISPLAY:-vnc=:1}"

args=(
  -machine q35,accel=tcg
  -m "$memory"
  -smp "$cpus"
  -cdrom /opt/chimera-ii-os.iso
  -boot d
  -vga std
  -display "$display"
  -serial stdio
  -monitor none
  -no-reboot
  -no-shutdown
)

case "$firmware" in
  bios)
    ;;
  uefi)
    code="${OVMF_CODE:-}"
    vars="${OVMF_VARS:-}"
    if [[ -z "$code" ]]; then
      for candidate in /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd /usr/share/ovmf/OVMF_CODE.fd; do
        if [[ -s "$candidate" ]]; then code="$candidate"; break; fi
      done
    fi
    if [[ -z "$vars" ]]; then
      for candidate in /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd /usr/share/ovmf/OVMF_VARS.fd; do
        if [[ -s "$candidate" ]]; then vars="$candidate"; break; fi
      done
    fi
    [[ -s "$code" && -s "$vars" ]] || { echo "UEFI requested but matching OVMF CODE/VARS files were not found" >&2; exit 2; }
    cp "$vars" /tmp/OVMF_VARS.fd
    args+=(
      -drive "if=pflash,format=raw,unit=0,readonly=on,file=$code"
      -drive "if=pflash,format=raw,unit=1,file=/tmp/OVMF_VARS.fd"
    )
    ;;
  *)
    echo "FIRMWARE must be bios or uefi (received: $firmware)" >&2
    exit 2
    ;;
esac

exec qemu-system-x86_64 "${args[@]}"
