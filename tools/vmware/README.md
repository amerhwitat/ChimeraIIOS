# VMware support

Chimera II OS uses UEFI/EFI firmware, a virtual disk, vmxnet3 networking, xHCI USB, and SVGA graphics in the generated VMX. This is suitable for VMware Workstation/Fusion and can be imported into VMware environments; exact hardware-version/device availability depends on the VMware product and host.

The current native boot contract is Koronos ELF via the ISO bootloader chain. Legacy GRUB entries that reference /vmlinuz or /initrd.img are not used.

## Workstation memory/pagefile preflight

The Windows error:

`Could not create anonymous paging file for 4388 MB: The paging file is too small for this operation to complete.`

is a host resource/Windows virtual-memory problem, not evidence that the Chimera ISO is corrupt. Broadcom's Workstation guidance calls out host memory and free host filesystem space as prerequisites for powering on a VM.

Run from an elevated PowerShell window:

```powershell
.\tools\vmware\chimera-vmware-preflight.ps1 -VmxPath 'D:\VMs\ChimeraIIOS\ChimeraIIOS.vmx'
```

The preflight reports VM memory, free space on the VMX filesystem, free physical RAM, current Windows pagefile allocation/usage, and `mainmem.useNamedFile`.

### Recommended repair

Enable a System Managed pagefile:

```powershell
.\tools\vmware\chimera-vmware-preflight.ps1 -VmxPath 'D:\VMs\ChimeraIIOS\ChimeraIIOS.vmx' -FixPageFile
```

Reboot Windows after changing the pagefile, then retry VMware.

If the error persists, explicitly use a named VMware memory file; the tool creates a VMX backup first:

```powershell
.\tools\vmware\chimera-vmware-preflight.ps1 -VmxPath 'D:\VMs\ChimeraIIOS\ChimeraIIOS.vmx' -FixNamedMemoryFile
```

The backup is saved beside the VMX as `.vmx.chimera-backup`.

Do not blindly increase VM RAM. If host free RAM is low, close other VMs/applications or reduce the VM allocation. Also ensure the filesystem containing the VMX has free space at least comparable to the VM's configured virtual memory; more headroom is preferable.

For the attached failure, VMware requested 4388 MB. A safe recovery sequence is: shut down other VMs, verify free disk space, enable a System Managed pagefile, reboot Windows, retry VMware, then use `-FixNamedMemoryFile` only if necessary. Do not delete VMDKs or snapshots as a first response to this particular error.
