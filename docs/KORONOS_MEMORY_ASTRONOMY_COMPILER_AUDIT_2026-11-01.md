# Koronos memory, astronomy catalog and compiler parity update — 2026-11-01

## Physical memory uplift

The previous 4-GiB physical frame ceiling has been raised to an initial 64-GiB direct-map window in the x86-64 Koronos branch.

- `KORONOS_FRAME_PHYS_LIMIT`: 64 GiB (`0x1000000000`).
- The 4-KiB frame bitmap now tracks 16,777,216 frames; the free and allocated bitmaps use 4 MiB total static storage.
- The 32-bit Multiboot2 entry builds 64 one-GiB PDPT mappings with 32,768 2-MiB identity leaves, preserving physical address bits above 4 GiB in the high PDE dword.
- Address-space cloning copies all 64 page directories.
- User virtual mappings start at 64 GiB, above the identity/direct map.
- `kernel/tests/frame_allocator_highmem_test.cpp` supplies a synthetic Multiboot2 map with usable RAM above 4 GiB and verifies high physical frame allocation, contiguous allocation and freeing.
- `kernel/build-koronos.sh` now runs that host regression on each Koronos build.

This is not unlimited RAM support. It is an initial 64-GiB window matching the x86-64 minimum 36-bit physical address width. More than 64 GiB requires CPUID-derived physical width, dynamic/sparse page-table mapping, NUMA-aware zones and a scalable PFN metadata model. The synthetic regression does not replace a QEMU test with more than 4 GiB of real RAM that writes/reads/frees an allocated frame above 4 GiB. Do not claim production high-memory validation until that test passes.

## Linux and Windows comparison

Linux x86-64 uses a high-half direct map, separate user mappings, physical-memory models (including SPARSEMEM for discontiguous/large systems), zones and a buddy allocator with per-CPU page sets. Windows x64 separates process virtual address spaces from physical RAM and manages PFN records, working sets and paging-backed commit. Koronos now has a larger identity map and fixed bitmaps, but does not yet have Linux/Windows-class virtual memory, demand paging, swapping/pagefile, NUMA, hot-add/remove, per-CPU caches, zone/DMA allocation or memory reclaim.

References:
- Linux x86-64 memory map: https://kernel.org/doc/html/latest/arch/x86/x86_64/mm.html
- Linux physical memory model: https://www.kernel.org/doc/html/latest/mm/memory-model.html
- Linux physical memory/allocator: https://docs.kernel.org/mm/physical_memory.html
- Windows virtual/physical memory: https://learn.microsoft.com/en-us/windows/win32/memory/virtual-address-space-and-physical-storage
- Windows memory management: https://learn.microsoft.com/en-us/windows/win32/memory/about-memory-management

## Astronomy applications

Added six upstream open-source projects to `desktop/optional_apps_catalog.json`:

| App | Purpose | License | Build |
|---|---|---|---|
| Stellarium | Real-time planetarium | GPL-2.0-or-later | CMake |
| KStars + Ekos | Planetarium, observation planner, telescope/astrophotography | GPL-2.0-or-later | CMake |
| Celestia | 3D space simulator | GPL-2.0-or-later | CMake |
| Gaia Sky | Scientific 3D universe visualization | MPL-2.0 | Gradle/Java |
| Siril | Astrophotography image processing | GPL-3.0-or-later | CMake |
| Gpredict | Satellite tracking | GPL-2.0-or-later | Autotools |

The entries link to upstream projects and list build dependencies. They are catalog-only: no native Koronos package, port, successful compile, or runnable application is claimed. Relevant upstream projects:
- https://stellarium.org/
- https://apps.kde.org/kstars/
- https://celestiaproject.space/
- https://gaiasky.space/
- https://siril.org/
- https://github.com/csete/gpredict

## Compiler parity

The Koronos build uses selectable GCC/G++ and Clang/Clang++ toolchains (plus NASM and GNU ld). This branch adds a high-memory allocator host test to the build script. A GCC/Clang host compiler build is not a self-hosted build: neither ChimeraIIOS nor OctavianOS has yet proven that its own booted native compiler can compile these third-party GUI applications. Porting Qt/KDE, GTK, OpenGL, Java and scientific dependencies remains prerequisite work.

## Release gates

- Build the freestanding kernel and run the high-memory regression with GCC and Clang.
- Add QEMU >4-GiB runtime memory read/write/free validation.
- Run BIOS and UEFI boot matrices.
- Keep astronomy apps marked unavailable until a native package, dependencies, successful build, desktop launch and license notices are verified.
- Do not publish a production ISO from source-level or synthetic-test evidence alone.


## Follow-up: real high-memory access probe

The kernel now exposes `koronos_frame_allocator_highmem_self_test()`. On a machine with usable memory above 4 GiB it allocates a frame above 4 GiB, writes and reads two 64-bit patterns through the identity/direct map, and frees the frame. If no usable RAM exists above 4 GiB the probe reports a skip; if the read/write/free test fails, Koronos marks frame initialization failed so the address-space backend remains disabled. Both repositories' Koronos boot workflows now request a 5-GiB QEMU guest and require the high-memory pass marker. The Octavian native build workflow also rebuilds with Clang/Clang++ after GCC/G++ and runs the synthetic allocator regression.


## Desktop and application-framework comparison

| Area | Windows implementation | Linux desktop implementation | Current Chimera/Octavian implementation |
|---|---|---|---|
| Shell/desktop | Explorer shell, Start menu, taskbar and Win32 window manager | GNOME Shell/KDE Plasma over Wayland or X11 | Aurora and Marine are HTML/CSS/JS desktop prototypes; Marine now exposes astronomy project links and Aurora consumes the optional-app catalog |
| App discovery | Start menu, MSIX/winget and registered application links | XDG desktop entries, package managers, Flatpak/AppImage and portals | JSON optional-app catalog with explicit external-provider/catalog-only states; no native astronomy package provider yet |
| Window/compositor | DWM, Win32 windowing and graphics stack | Wayland compositor, XDG portals and toolkit backends | Native compositor/window protocol and GPU driver integration remain incomplete |
| Background services | Windows Service Control Manager | systemd service units and D-Bus activation | Koronos service manifest/dependency state only; full process supervision is not complete |
| Astronomy apps | Windows builds exist for Stellarium, KStars, Celestia, Gaia Sky and Siril | Linux packages/source builds exist for the listed projects | Upstream links and build recipes are catalogued; no app is yet ported/compiled/launched natively |

The comparison is architectural rather than a claim of binary compatibility. Windows uses the Service Control Manager to maintain service records and start/stop service and driver processes; Linux VFS and desktop stacks rely on process-context filesystem calls, XDG launch metadata and compositor protocols. The OS desktop pages should not be described as equivalent to Explorer, GNOME or Plasma until their native window manager, compositor, accessibility, input, file associations, application lifecycle and package-provider contracts are implemented and tested.

References: https://learn.microsoft.com/en-us/windows/win32/services/service-control-manager ; https://docs.kernel.org/filesystems/vfs.html ; https://apps.kde.org/kstars/ ; https://stellarium.org/ .
