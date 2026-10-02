# Chimera Mobile Flash / Recovery

Chimera Mobile provides an owner-authorized, device-detection and firmware-recovery framework for Android and iOS-class devices.

## Supported workflow

- USB device detection
- Android ADB/fastboot information
- OEM-supported bootloader-unlock handoff
- Explicit-partition Android flashing
- Android bootloader/recovery reboot
- iOS device identification when `libimobiledevice` is installed
- Handoff to Apple's supported recovery/restore workflow
- Vendor recovery workflows where authorization is available

The framework is designed for Samsung, Xiaomi/Redmi, Huawei/Honor, Oppo/OnePlus/Realme, Vivo/iQOO, Meizu, ZTE, TCL, Lenovo/Motorola, Google Pixel, Sony, LG and other devices **only where their documented interfaces permit the requested operation**. Device-specific protocols and signed firmware must not be guessed.

## Security boundary

The tool does not bypass or remove FRP, Google account protection, Apple Activation Lock/iCloud lock, MDM/enterprise controls, carrier restrictions, stolen-device protections, OEM authorization servers, or signed-firmware verification. Those controls require the owner's/vendor's authorization.

Android's documented bootloader model distinguishes LOCKED and UNLOCKED states, and state transitions can wipe user data. citeturn0search6turn0search2 Xiaomi's current documentation likewise warns that unlocking can erase data and requires account/device authorization. citeturn0search0 Samsung documents Smart Switch Emergency Software Recovery for failed software updates. citeturn0search1 Apple documents supported backup and restore workflows rather than an unlock bypass. citeturn0search5

## Examples

```bash
./tools/mobile/chimera-mobile-flash.sh detect
./tools/mobile/chimera-mobile-flash.sh android-info
./tools/mobile/chimera-mobile-flash.sh android-unlock
./tools/mobile/chimera-mobile-flash.sh android-flash boot.img boot
./tools/mobile/chimera-mobile-flash.sh ios-info
```

Always verify model, region, bootloader state, firmware version, partition layout and signed-image compatibility before flashing. Backup first.
