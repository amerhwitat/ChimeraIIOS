#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/vmware/chimera-vmware.sh

Usage:
  tools/vmware/chimera-vmware.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO="${CHIMERA_ISO:-$ROOT/build/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso}"
VM_DIR="${CHIMERA_VMWARE_DIR:-$ROOT/build/vmware}"
VMX="${CHIMERA_VMX:-$VM_DIR/chimera-ii-os.vmx}"
DISK="${CHIMERA_VMDK:-$VM_DIR/chimera-ii-os.vmdk}"
NVRAM="${CHIMERA_NVRAM:-$VM_DIR/chimera-ii-os.nvram}"
# Conservative defaults for low-level kernel validation on VMware Workstation.
MEM="${CHIMERA_VM_MEMORY_MB:-3072}"
CPUS="${CHIMERA_VM_CPUS:-1}"
# Chimera's current boot chain is validated most reliably through legacy BIOS.
# Set CHIMERA_VM_FIRMWARE=efi after the UEFI path has been independently tested.
FIRMWARE="${CHIMERA_VM_FIRMWARE:-bios}"
HW_VERSION="${CHIMERA_VM_HW_VERSION:-18}"

case "$FIRMWARE" in bios|efi) ;; *) echo "FIRMWARE must be bios or efi" >&2; exit 2 ;; esac
[[ "$MEM" =~ ^[0-9]+$ ]] || { echo "CHIMERA_VM_MEMORY_MB must be an integer" >&2; exit 2; }
(( MEM >= 1024 && MEM % 4 == 0 )) || { echo "VM memory must be >=1024 MB and a multiple of 4 MB" >&2; exit 2; }
[[ "$CPUS" =~ ^[0-9]+$ ]] || { echo "CHIMERA_VM_CPUS must be an integer" >&2; exit 2; }
(( CPUS >= 1 && CPUS <= 2 )) || { echo "For kernel validation, CHIMERA_VM_CPUS must be 1 or 2" >&2; exit 2; }
[[ -s "$ISO" ]] || { echo "ISO not found: $ISO" >&2; exit 1; }
mkdir -p "$VM_DIR"

# Workstation 16-compatible conservative VMX. Keep the first boot single-vCPU,
# BIOS, non-accelerated graphics and explicit triple-fault diagnostics so a
# kernel/boot fault does not become an opaque Workstation crash.
cat >"$VMX" <<EOF
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "$HW_VERSION"
memsize = "$MEM"
numvcpus = "$CPUS"
cpuid.coresPerSocket = "1"
guestOS = "otherlinux-64"
firmware = "$FIRMWARE"

mainmem.useNamedFile = "TRUE"
monitor.suspend_on_triplefault = "TRUE"

sata0.present = "TRUE"
sata0:0.present = "TRUE"
sata0:0.deviceType = "disk"
sata0:0.fileName = "$(basename "$DISK")"
sata0:1.present = "TRUE"
sata0:1.deviceType = "cdrom-image"
sata0:1.fileName = "$ISO"
sata0:1.startConnected = "TRUE"
sata0:1.clientDevice = "FALSE"

# BIOS is the default because the current low-level Chimera boot chain is
# multiboot/legacy-oriented. The UEFI ISO assets remain available for later
# UEFI validation.
bios.bootOrder = "cdrom,hdd"

ethernet0.present = "TRUE"
ethernet0.virtualDev = "e1000e"
ethernet0.connectionType = "nat"
usb.present = "TRUE"
usb_xhci.present = "TRUE"

# Avoid host accelerated 3D while diagnosing vCPU/kernel faults.
svga.present = "TRUE"
svga.autodetect = "TRUE"
svga.vramSize = "67108864"
mks.enable3d = "FALSE"

chipset.useAcpi = "TRUE"

nvram = "$(basename "$NVRAM")"
efi.secureBoot.enabled = "FALSE"

# Do not expose nested virtualization during initial kernel validation.
vhv.enable = "FALSE"
EOF

if command -v vmware-vdiskmanager >/dev/null 2>&1 && [[ ! -e "$DISK" ]]; then
  vmware-vdiskmanager -c -s 32G -a lsilogic -t 0 "$DISK"
fi

printf '%s\n' "Generated VMware VMX: $VMX"
printf '%s\n' "Firmware: $FIRMWARE; hardware: v$HW_VERSION; memory: ${MEM}MB; vCPUs: $CPUS; ISO: $ISO"
printf '%s\n' "UEFI NVRAM: $NVRAM; NIC: e1000e; USB: xHCI; 3D: disabled"
printf '%s\n' "VM memory uses a named VMware memory file; Windows still needs sufficient host RAM/pagefile/disk resources."
printf '%s\n' "Triple-fault diagnostics enabled: monitor.suspend_on_triplefault=TRUE"
printf '%s\n' "For UEFI validation use CHIMERA_VM_FIRMWARE=efi only after BIOS boot is confirmed."
