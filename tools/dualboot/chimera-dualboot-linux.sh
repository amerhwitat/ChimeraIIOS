#!/usr/bin/env bash
set -euo pipefail
DRY_RUN=1; TARGET=""; ESP=""; ROOTDEV=""
while [[ $# -gt 0 ]]; do
 case "$1" in --apply) DRY_RUN=0;; --target) TARGET="$2"; shift;; --esp) ESP="$2"; shift;; --root) ROOTDEV="$2"; shift;; --help) echo "Usage: $0 --target DISK --esp MOUNT --root DEVICE [--apply]"; exit 0;; *) echo "Unknown option: $1" >&2; exit 2;; esac; shift
done
[[ -n "$TARGET" ]] || { echo "--target is required" >&2; exit 2; }
lsblk -o NAME,PATH,SIZE,FSTYPE,TYPE,MOUNTPOINTS,PARTUUID,PARTLABEL "$TARGET"
if [[ "$DRY_RUN" == 1 ]]; then echo "DRY RUN: no disk, filesystem, EFI, or boot changes."; exit 0; fi
[[ $EUID -eq 0 ]] || { echo "--apply requires root" >&2; exit 4; }
[[ -d /sys/firmware/efi ]] || { echo "Booted system is not UEFI" >&2; exit 5; }
command -v efibootmgr >/dev/null || { echo "efibootmgr required" >&2; exit 6; }
[[ -n "$ESP" && -d "$ESP" ]] || { echo "Mounted ESP required with --esp" >&2; exit 7; }
[[ -n "$ROOTDEV" && -b "$ROOTDEV" ]] || { echo "Existing root partition required; automatic partition creation is disabled." >&2; exit 8; }
[[ -n "${CHIMERA_INSTALL_ROOT:-}" ]] || { echo "Set CHIMERA_INSTALL_ROOT to a staged system tree." >&2; exit 9; }
mkdir -p "$ESP/EFI/CHIMERA"; cp -a "$CHIMERA_INSTALL_ROOT/." "$ESP/EFI/CHIMERA/"; sync
echo "Chimera payload staged at $ESP/EFI/CHIMERA. Final filesystem/boot entry creation remains in the installer UI."
