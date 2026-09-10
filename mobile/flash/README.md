# Mobile flashing

Flashing is device-specific and must be performed only after the exact profile is validated.

1. Identify the exact model and SoC.
2. Confirm the bootloader state and OEM unlock policy.
3. Back up user data.
4. Validate the profile and partition map.
5. Build/sign the exact image with authorized keys.
6. Enter the device's documented fastboot/recovery/vendor mode.
7. Verify the target partition before writing.
8. Flash only the profile-defined partitions.
9. Reboot and verify AVB/boot state.

The repository intentionally does not contain a universal destructive flashing command or private signing keys.
