# Chimera II Emulator Stack

The emulator subsystem is registered by `config/aurora/emulators.json` and presented through the Aurora.Emulator window contract.

The build pipeline is source-first: `tools/build-emulator-stack.sh`.

ROM distribution is license-gated. Commercial ROMs and proprietary BIOS images are not bundled. User-owned dumps are loaded from `~/Games/ROMs` and BIOS from `~/Games/BIOS`.

Video output uses Aurora display backends and can fall back from GPU acceleration to software rendering.
