# CPU-aware ISO build profiles

The ISO builder detects the build host with `uname -m`, accepts an explicit
`CHIMERA_TARGET_ARCH`, logs both values, and never silently treats the host CPU
as the target CPU. Output ISO filenames include the target architecture.

## Implemented profile

| Target | Boot pipeline | Media filesystem | Status |
| --- | --- | --- | --- |
| `x86_64` | Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora | ISO9660 + El Torito BIOS/UEFI boot images; SquashFS compressed live rootfs | Supported by the current boot-artifact pipeline, subject to build-time verification |

The SquashFS worker default follows the detected online CPU count. Override it
with `CHIMERA_SQUASHFS_PROCESSORS` when memory or storage throughput requires a
limit. The build remains configurable with `CHIMERA_MEDIA_FS_PROFILE`; currently
only `iso9660+squashfs` is implemented.

## Detected but not yet buildable as an ISO

| Target | Intended media contract | Why the current ISO build stops |
| --- | --- | --- |
| `aarch64` | ARM64 UEFI removable-media boot (FAT EFI System Partition where required by device firmware) plus a supported rootfs such as SquashFS | Current Koronos/Jasper/Spit Fire build and GRUB loader generation are x86_64-specific |
| `riscv64` | Platform-specific UEFI/OpenSBI boot media and a supported rootfs | No complete architecture-specific boot-artifact and firmware verification pipeline is wired into this script |
| `i386` | BIOS boot media with an architecture-matched kernel and loader | Current kernel/boot-artifact build is x86_64-specific |

For these targets the script fails early rather than producing a misleading ISO.
Detection is not a claim of support. A target becomes supported only after its
kernel, boot stages, loader paths, firmware boot entries, media filesystem,
installer payload, and boot verification are architecture-matched and tested.

## Invocation

```sh
# Native x86_64 build; defaults to detected CPU and media profile
./build-chimera-iso.sh --clean-state --storage-auto

# Explicit target/profile (the current implementation accepts x86_64 only)
CHIMERA_TARGET_ARCH=x86_64 CHIMERA_MEDIA_FS_PROFILE=iso9660+squashfs \
  ./build-chimera-iso.sh --resume
```

Final ISO naming is `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`; the matching
SHA-256 file uses the same base name.
