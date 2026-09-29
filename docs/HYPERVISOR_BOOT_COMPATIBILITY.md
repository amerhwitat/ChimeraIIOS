# Chimera II OS ISO — Hypervisor Boot Compatibility

## ISO contract

The comprehensive ISO is built as an El Torito BIOS + UEFI CD/DVD image:

`ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`

The boot chain inside the ISO is:

`firmware -> Spit Fire/Jasper/GRUB -> Koronos Multiboot2 -> Live/Installer/Aurora`

The same ISO is intended for physical CD/DVD/virtual-DVD boot and does not require a Linux `vmlinuz` guest kernel.

## Hyper-V

### Generation 1

Use Generation 1 for the legacy BIOS path. The helper configures the virtual DVD as the first boot device.

```powershell
.\tools\hyperv\chimera-hyperv.ps1 -Generation 1 -Start
```

### Generation 2

Use Generation 2 for the UEFI path:

```powershell
.\tools\hyperv\chimera-hyperv.ps1 -Generation 2 -Start
```

The helper disables Secure Boot by default because the current Chimera `BOOTX64.EFI` is not signed by Microsoft. Hyper-V Generation 2 Secure Boot is enabled by default and validates UEFI boot components; Microsoft documents the Microsoft UEFI Certificate Authority template for supported Linux guests. A future signed Chimera shim can re-enable Secure Boot as a separate release gate.

### Hyper-V device assumptions

Koronos should see virtual hardware through its generic PCI/ACPI discovery path. The important boot devices are:

- virtual DVD/ISO
- virtual SCSI/IDE storage as supplied by the selected generation
- Hyper-V virtual network adapter after the OS has booted
- UEFI GOP on Generation 2

## VMware

The VMware helper defaults to EFI:

```bash
./tools/vmware/chimera-vmware.sh
```

For the legacy BIOS path:

```bash
CHIMERA_VM_FIRMWARE=bios ./tools/vmware/chimera-vmware.sh
```

The generated VMX attaches the Chimera ISO as a virtual CD/DVD and exposes:

- ACPI
- SATA storage
- vmxnet3 network
- xHCI USB
- VMware SVGA
- EFI or legacy BIOS according to `CHIMERA_VM_FIRMWARE`

Secure Boot is explicitly disabled in the generated VMware VMX until a signed Chimera EFI shim is available.

## Graphics

GRUB now requests `gfxpayload=keep` and uses a fallback sequence suitable for virtual graphics devices. Hyper-V Generation 2 and VMware EFI should preserve the firmware framebuffer/GOP into the Koronos boot handoff. Legacy BIOS paths retain GRUB's Bochs/Cirrus-compatible video modules as fallback.

## Validation

After building the ISO:

```bash
./tools/hypervisor/validate-chimera-iso.sh build/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
```

The validator checks the ISO's El Torito system-area report for both BIOS and UEFI boot paths and validates the Koronos Multiboot2 payload when the build tree is available.

## Secure Boot status

Secure Boot is deliberately **not** claimed for the current ISO. Enabling Secure Boot requires a signed EFI boot chain. The hypervisor helpers therefore optimize for reliable boot of the current research ISO and make Secure Boot an explicit future signing/release step rather than silently configuring a VM that cannot boot.
