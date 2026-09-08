# Chimera II Internet Source Catalog and Link-Depth Map

This catalog records authoritative/open-source sources used by the installer and architecture work. `depth` is a planned traversal depth from the source root; the installer documentation parser should cap automated traversal at 10 to prevent unbounded crawling.

| depth | domain/source | purpose |
|---:|---|---|
| 0 | uefi.org/specifications | UEFI/ACPI platform standards |
| 0 | docs.kernel.org | kernel/device/storage/network interfaces |
| 0 | kernel.googlesource.com/.../linux-firmware | firmware inventory and licensing metadata |
| 0 | github.com/cateee/lkddb | Linux hardware/driver database |
| 0 | canonical-subiquity.readthedocs-hosted.com | declarative Linux installer/storage model |
| 0 | debian.org/releases | firmware detection and installer behavior |
| 0 | docs.freebsd.org/en/books/handbook | BSD storage/network/boot compatibility |
| 0 | wayland.freedesktop.org | Wayland protocol |
| 0 | wayland.pages.freedesktop.org/weston | compositor/backend reference |
| 0 | docs.mesa3d.org | GPU/OpenGL/Vulkan userspace stack |
| 0 | spdk.io/doc | NVMe, block devices, userspace storage |
| 0 | openzfs.github.io/openzfs-docs | ZFS/RAIDZ |
| 0 | learn.microsoft.com/windows-hardware/drivers | WDK/driver model/signing |
| 0 | learn.microsoft.com/windows-hardware/test/hlk | Windows hardware compatibility testing |
| 0 | catalog.update.microsoft.com | signed Microsoft driver/update catalog |
| 0 | learn.microsoft.com/windows-server/storage | Storage Spaces, ReFS, NTFS, server storage |
| 0 | github.com/systemd/systemd | udev, predictable network naming, service compatibility |

## Traversal policy

1. Follow only documentation/reference links from an allowlisted source.
2. Normalize and deduplicate URLs.
3. Stop at depth 10.
4. Prefer canonical documentation over mirrors.
5. Record retrieval date, title and license where available.
6. Never download or execute arbitrary binaries as part of crawling.
7. Firmware/driver packages enter the installer only after signature, hardware-ID and license checks.
8. Search engines are discovery mechanisms, not trust roots.

## Search coverage

Research for this integration used both available web search modes (fast and slow) and direct authoritative source retrieval. No honest implementation can claim to have searched literally every Internet search engine or every website; the trust model therefore favors primary standards bodies, kernel/distribution documentation, Microsoft documentation/catalogs and established open-source projects.
