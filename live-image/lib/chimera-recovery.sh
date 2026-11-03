#!/usr/bin/env bash
set -euo pipefail
echo
echo "=== RESCUE SHELL — Chimera / Octavian Recovery Environment ==="
echo "No disk is modified automatically. Inspection is read-only; repair requires typed confirmation."
echo
while true; do
  echo "Recovery actions:"
  select action in "Show disks and partitions" "Show boot and kernel logs" "Check a filesystem (explicit device required)" "Open root shell" "Reboot"; do
    case "$REPLY" in
      1) lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS; break ;;
      2) journalctl -b --no-pager -n 250 || dmesg -T | tail -n 250; break ;;
      3)
        lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS
        read -r -p "Exact filesystem device (blank cancels): " device
        if [[ -z "$device" ]]; then echo "Cancelled."; break; fi
        if [[ ! -b "$device" ]]; then echo "Refusing: $device is not a block device."; break; fi
        read -r -p "Run fsck -f on $device? This may modify filesystem metadata. Type CHECK to continue: " confirm
        if [[ "$confirm" == "CHECK" ]]; then sudo fsck -f "$device"; else echo "Cancelled."; fi
        break ;;
      4) exec sudo -i ;;
      5) systemctl reboot ;;
      *) echo "Choose a listed action."; break ;;
    esac
  done
done
