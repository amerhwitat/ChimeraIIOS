#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO="${CHIMERA_ISO:-$ROOT/build/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso}"
VM_DIR="${CHIMERA_VMWARE_DIR:-$ROOT/build/vmware}"
VMX="${CHIMERA_VMX:-$VM_DIR/chimera-ii-os.vmx}"
DISK="${CHIMERA_VMDK:-$VM_DIR/chimera-ii-os.vmdk}"
MEM="${CHIMERA_VM_MEMORY_MB:-4096}"
CPUS="${CHIMERA_VM_CPUS:-2}"
FIRMWARE="${CHIMERA_VM_FIRMWARE:-efi}"

case "$FIRMWARE" in efi|bios) ;; *) echo "FIRMWARE must be efi or bios" >&2; exit 2 ;; esac
[[ -s "$ISO" ]] || { echo "ISO not found: $ISO" >&2; exit 1; }
mkdir -p "$VM_DIR"

# VMware Workstation/Fusion/Player can boot the same ISO through either the
# legacy BIOS firmware or UEFI. UEFI is the default and maps directly to the
# x86_64-efi El Torito path produced by grub-mkrescue.
cat >"$VMX" <<EOF
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "20"
memsize = "$MEM"
numvcpus = "$CPUS"
guestOS = "otherlinux-64"
firmware = "$FIRMWARE"

sata0.present = "TRUE"
sata0:0.present = "TRUE"
sata0:0.deviceType = "disk"
sata0:0.fileName = "$(basename "$DISK")"
sata0:1.present = "TRUE"
sata0:1.deviceType = "cdrom-image"
sata0:1.fileName = "$ISO"
sata0:1.startConnected = "TRUE"
sata0:1.clientDevice = "FALSE"

ethernet0.present = "TRUE"
ethernet0.virtualDev = "vmxnet3"
ethernet0.connectionType = "nat"
usb.present = "TRUE"
usb_xhci.present = "TRUE"
svga.present = "TRUE"
svga.autodetect = "TRUE"
svga.vramSize = "134217728"
chipset.useAcpi = "TRUE"

# Keep Secure Boot off until a Microsoft/UEFI-signed Chimera shim is available.
efi.secureBoot.enabled = "FALSE"
EOF

if command -v vmware-vdiskmanager >/dev/null 2>&1 && [[ ! -e "$DISK" ]]; then
  vmware-vdiskmanager -c -s 32G -a lsilogic -t 0 "$DISK"
fi

printf '%s\n' "Generated VMware VMX: $VMX"
printf '%s\n' "Firmware: $FIRMWARE; ISO: $ISO; NIC: vmxnet3; USB: xHCI; graphics: SVGA"
printf '%s\n' "The CD/DVD is first boot media; firmware can be changed by editing firmware=efi|bios."
