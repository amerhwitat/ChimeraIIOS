# Aurora Emulators panel

The registry in `emulator-registry.json` is the source of truth for Sakhr entries exposed by the Aurora desktop Emulators panel.

Current entries:
- Sakhr AX-170
- Sakhr AX-230

Each entry has a dedicated launcher and exact ROM SHA-1 requirements. ROM binaries are intentionally not committed to the public ChimeraIIOS repository. The panel reports `requires-user-roms` until verified ROMs are present.

## Provisioning

1. Obtain the ROMs using `amerhwitat/BizX/emulators/sakhr/roms/fetch_sakhr_roms.sh`.
2. Install OpenMSX or MAME in Chimera II OS.
3. Launch from Aurora -> Emulators -> Sakhr.

This design lets the panel expose emulator binaries and firmware state without silently redistributing historical firmware.
