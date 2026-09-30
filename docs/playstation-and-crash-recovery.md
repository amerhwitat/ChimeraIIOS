# PlayStation and crash recovery

## PlayStation emulation

Chimera II provides an extensible PlayStation center for PSX, PS2, PS3, PS4 and experimental PS5 targets.

Open-source emulator projects are built or staged by tools/build-emulator-stack.sh:

- PSX: PCSX-Redux
- PS2: PCSX2
- PS3: RPCS3
- PS4: shadPS4
- PS5: experimental target registry; no proprietary firmware is bundled.

PCSX2 is GPL-3.0-or-later and requires a BIOS dump from a legitimately owned PS2 console. RPCS3 is GPL-2.0-only. shadPS4 is GPL-2.0 and describes itself as an early PS4 emulator; its firmware modules must be dumped from a legally owned PS4. [Sources: PCSX2 README, RPCS3 README, shadPS4 README]

## Final Fantasy

Commercial Final Fantasy source code, ROMs, ISOs, discs, BIOS/firmware or proprietary assets are not redistributed by Chimera II. The emulator center supports importing the user's legally owned game dumps.

Free/open-source PSX homebrew and public-domain demos can be placed in the legal ROM area and used for validation.

## Runtime compression

Built emulator executables can be compressed as Zstandard payloads. chimera-xexec decompresses them into a private runtime cache before execution. The compressed bytes themselves are never executed.

## Crash handling

Fatal-state infrastructure provides:

- Screen of Death UI contract.
- /var/crash/chimera/<UTC>/ crash bundles.
- /var/log/mesgs capture and archive.
- process/service/hardware/kernel metadata.
- optional privileged memory capture through a native kernel crash provider.
- register/stack dump hooks reserved for the native Koronos panic path.
- configurable retention.

A complete physical-RAM image is intentionally delegated to a privileged Koronos crash-dump provider rather than pretending /proc/kcore is a complete physical-memory dump. This is required for a real bare-metal dump implementation.
