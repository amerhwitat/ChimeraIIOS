#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO="${CHIMERA_ISO:-$ROOT/build/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso}"
VM_DIR="${CHIMERA_VMWARE_DIR:-$ROOT/build/vmware}"
VMX="${CHIMERA_VMX:-$VM_DIR/chimera-ii-os.vmx}"
DISK="${CHIMERA_VMDK:-$VM_DIR/chimera-ii-os.vmdk}"
NVRAM="${CHIMERA_NVRAM:-$VM_DIR/chimera-ii-os.nvram}"
# 3 GiB is a safer default for Windows hosts while validating the low-level
# kernel. Override with CHIMERA_VM_MEMORY_MB=4096 when the host has sufficient
# RAM and a sufficiently large Windows pagefile.
MEM="${CHIMERA_VM_MEMORY_MB:-3072}"
# Workstation 16 is more reliable with a single virtual CPU while validating
# a new low-level kernel. Override with CHIMERA_VM_CPUS=2+ after first boot.
CPUS="${CHIMERA_VM_CPUS:-1}"
FIRMWARE="${CHIMERA_VM_FIRMWARE:-efi}"
HW_VERSION="${CHIMERA_VM_HW_VERSION:-18}"

case "$FIRMWARE" in efi|bios) ;; *) echo "FIRMWARE must be efi or bios" >&2; exit 2 ;; esac
[[ "$MEM" =~ ^[0-9]+$ ]] || { echo "CHIMERA_VM_MEMORY_MB must be an integer" >&2; exit 2; }
(( MEM >= 1024 && MEM % 4 == 0 )) || { echo "VM memory must be >=1024 MB and a multiple of 4 MB" >&2; exit 2; }
[[ -s "$ISO" ]] || { echo "ISO not found: $ISO" >&2; exit 1; }
mkdir -p "$VM_DIR"

# VMware Workstation 16 uses virtual hardware version 18. Keep the generated
# VMX conservative so a newer Workstation-generated hardware profile does not
# introduce unsupported virtual hardware into Workstation 16.
cat >"$VMX" <<EOF
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "$HW_VERSION"
memsize = "$MEM"
numvcpus = "$CPUS"
cpuid.coresPerSocket = "1"
guestOS = "otherlinux-64"
firmware = "$FIRMWARE"

# Workstation memory allocation: prefer a named VM memory file rather than
# relying solely on anonymous host paging. This is a recovery-friendly setting
# for the 'Could not create anonymous paging file' failure seen on Windows.
mainmem.useNamedFile = "TRUE"

sata0.present = "TRUE"
sata0:0.present = "TRUE"
sata0:0.deviceType = "disk"
sata0:0.fileName = "$(basename "$DISK")"
sata0:1.present = "TRUE"
sata0:1.deviceType = "cdrom-image"
sata0:1.fileName = "$ISO"
sata0:1.startConnected = "TRUE"
sata0:1.clientDevice = "FALSE"

# Explicitly keep the ISO as the first installation/recovery medium.
bios.bootOrder = "cdrom,hdd"

ethernet0.present = "TRUE"
ethernet0.virtualDev = "e1000e"
ethernet0.connectionType = "nat"
usb.present = "TRUE"
usb_xhci.present = "TRUE"
svga.present = "TRUE"
svga.autodetect = "TRUE"
svga.vramSize = "134217728"
chipset.useAcpi = "TRUE"

# UEFI firmware and persistent NVRAM. Secure Boot remains disabled because
# Chimera currently uses an unsigned GRUB/Spit Fire chain.
nvram = "$(basename "$NVRAM")"
efi.secureBoot.enabled = "FALSE"

# Avoid VMware accelerated-virtualization features that are unnecessary for
# the initial kernel/boot validation and can expose host Hyper-V conflicts.
vhv.enable = "FALSE"
EOF

if command -v vmware-vdiskmanager >/dev/null 2>&1 && [[ ! -e "$DISK" ]]; then
  vmware-vdiskmanager -c -s 32G -a lsilogic -t 0 "$DISK"
fi

printf '%s\n' "Generated VMware VMX: $VMX"
printf '%s\n' "Firmware: $FIRMWARE; hardware: v$HW_VERSION; memory: ${MEM}MB; vCPUs: $CPUS; ISO: $ISO"
printf '%s\n' "UEFI NVRAM: $NVRAM; NIC: e1000e; USB: xHCI; graphics: SVGA"
printf '%s\n' "VM memory uses a named VMware memory file; Windows still needs sufficient host RAM and disk/pagefile resources."
printf '%s\n' "For VMware Workstation 16, start with 3072MB/one vCPU. Increase CHIMERA_VM_MEMORY_MB only after the host preflight passes."
printf '%s\n' "On Windows, run tools/vmware/chimera-vmware-preflight.ps1 against this VMX before starting it."
