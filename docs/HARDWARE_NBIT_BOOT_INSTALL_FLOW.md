# Chimera II OS Hardware-Aware N-bit Execution and Boot Flow

## 1. Design contract

Koronos is the single native kernel. At startup it probes the underlying CPU/architecture and establishes the hardware profile before user-space compatibility services start.

Supported logical execution widths are:

- 8, 16, 32, 64 bits
- 128, 256, 512, 1024, 2048, 4096, 8192 bits through the Chimera execution/emulation layer

The hardware-native default is the exact native pointer/execution width reported by the active kernel architecture. On x86-64 and AArch64 this is normally 64-bit. Wider Chimera modes are not claimed to be native CPU modes; they are execution-layer modes.

## 2. Process model

N-bit width is a process property.

1. Koronos initializes the global hardware profile.
2. A process receives a requested width or the current policy default.
3. The process is classified as native, emulated/wide, or compatibility execution.
4. The process retains its own width; changing the desktop default does not rewrite an existing process address space or ABI.
5. Compatibility runtimes select their ABI width independently: Windows x86 uses 32-bit, Windows x64/ARM64 use 64-bit, and Linux/BSD/Darwin/Android/iOS use their declared ABI profiles.

## 3. Mixed-width communication

Processes never need identical register widths to communicate.

The IPC boundary carries:

- protocol version
- sender width
- receiver width
- payload bit length
- payload byte length
- sequence
- bounded payload pointer

The transport is width-neutral and uses a canonical byte representation. A 32-bit compatibility process can therefore exchange messages with 64-bit native processes and 128/256/512/1024/2048/4096/8192-bit Chimera execution processes.

ABI-specific pointers, handles and structures must remain inside their compatibility boundary; cross-process IPC uses the canonical transport instead of copying ABI-private layouts.

## 4. Boot execution order

### Bare metal / installed system

1. Firmware (BIOS/UEFI) initializes CPU and firmware tables.
2. Spit Fire performs the native bootstrap.
3. Jasper applies the boot policy and selects the requested profile.
4. GRUB2 provides filesystem/menu adaptation where configured.
5. Koronos is loaded as the Multiboot2 ELF kernel.
6. Koronos initializes early architecture state and the scheduler.
7. Koronos probes CPU architecture/features and establishes the hardware profile.
8. Koronos initializes the N-bit policy: "auto" selects the hardware-native width; manual policy may select another supported width.
9. Memory, framebuffer/GOP and device discovery initialize.
10. Drivers and MHAL start.
11. Spotnik, Nucleus, Hive, Kore and Aegis start.
12. Compatibility runtimes start for Windows/Linux/BSD/Darwin/Android/iOS as selected.
13. Aurora starts and exposes the desktop N-bit/compatibility controls.
14. User processes are created with their requested/default execution contexts.

### Live CD/DVD/USB

The Live GRUB entry loads:

- /boot/koronos/koronos.elf
- /boot/live/chimera-live-initramfs.img
- /boot/live/live-manifest.json
- /system/hardware/chimera-hardware-profile.json
- /system/hardware/compatibility-modes.json
- /system/hardware/nbit-policy.conf

Koronos then follows the same hardware discovery and N-bit initialization path before the Live Aurora session is started.

### Installer

Jasper's installer entry loads:

- /boot/koronos/koronos.elf
- /install/installer/installation.img
- installer manifest/contracts
- hardware profile
- compatibility profile
- N-bit policy

The installer performs hardware discovery, chooses the execution mode, prepares storage/boot entries, installs Koronos and its runtime modules, copies the N-bit/compatibility policy, validates the boot chain, and performs first-boot initialization.

## 5. Aurora desktop control

Aurora Settings exposes:

isa.nbit.width

Values:

- auto
- 8
- 16
- 32
- 64
- 128
- 256
- 512
- 1024
- 2048
- 4096
- 8192

auto selects the hardware-native best mode. Manual selection is persisted in /etc/chimera/nbit-policy.conf and is used as the policy for subsequent process/runtime initialization. Existing processes keep their current execution context.

The command-line control utility is:

chimera-hwmode show
chimera-hwmode best
chimera-hwmode set auto
chimera-hwmode set 64
chimera-hwmode set 8192

## 6. Compatibility boundaries

Compatibility is implemented above Koronos rather than by replacing the kernel scheduler.

- Windows: NT/Win32/PE compatibility boundary
- Linux: POSIX/Linux compatibility boundary
- BSD: POSIX/BSD compatibility boundary
- Darwin/macOS: Darwin compatibility boundary
- Android: Android ABI compatibility boundary
- iOS: iOS ABI compatibility boundary

Each runtime can use its native ABI width while communicating with other modes through the common IPC boundary.

## 7. Verification requirements

Before claiming a complete hardware boot result, verify:

1. Koronos ELF64 builds and contains the hardware/N-bit symbols.
2. Host hardware/N-bit unit tests pass.
3. CMake configure/build passes.
4. ISO staging contains all hardware profile, compatibility and policy files.
5. GRUB Live entries reference the policy modules.
6. Jasper installer entries reference the policy modules.
7. Installer and Live manifests are internally consistent.
8. QEMU/VM boot reaches Koronos hardware discovery.
9. Aurora can change the persistent N-bit policy.
10. A mixed-width IPC test passes between at least a lower-width compatibility context and a 64-bit native context.
11. Physical-hardware verification confirms CPU/firmware/driver discovery on the target machine.

No physical-hardware execution is implied by source/build verification alone.
