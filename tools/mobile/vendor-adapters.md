# Chimera Mobile Vendor Adapters

Chimera Mobile supports owner-authorized recovery, diagnostics, bootloader workflows, and firmware flashing where the vendor exposes a documented interface. Adapters must never bypass device-account, activation, enterprise, carrier, or anti-theft controls.

| Vendor/family | Supported interface | Chimera operation |
|---|---|---|
| Google Pixel / AOSP-compatible | ADB + fastboot | detect, bootloader state, authorized unlock handoff, explicit partition flashing |
| Samsung Galaxy | Samsung-supported recovery/service workflow | detect and recovery handoff; firmware package validation; no security bypass |
| Xiaomi / Redmi / POCO | fastboot + official unlock authorization | detect, authorization handoff, package validation, flashing after authorization |
| OnePlus / OPPO / Realme | fastboot/vendor-supported recovery | detection and authorized firmware workflow where available |
| Motorola / Lenovo | fastboot | detection, bootloader-state check, authorized unlock handoff, flashing |
| Sony Xperia | fastboot / vendor-supported tools | detection and authorized flashing |
| Huawei / Honor | vendor-supported recovery/service paths | detection and recovery handoff; no unauthorized bootloader bypass |
| Vivo / iQOO | vendor-supported recovery/service paths | detection and recovery handoff; no unauthorized security bypass |
| ZTE / TCL / Meizu | documented vendor recovery/fastboot interfaces | detection and authorized flashing |
| Apple iPhone / iPad | recovery mode + Apple Devices/Finder/libimobiledevice | detection, recovery entry, supported restore handoff |

## ROM handling

ROM packages are accepted only when the user supplies or explicitly selects an image intended for the detected model/variant. The tool validates the device identity and image metadata where available before offering a flash operation. It does not download or redistribute proprietary firmware without an appropriate license.

## Unlocking

Android bootloader unlocking is exposed only through the normal OEM-supported flow. Android's Verified Boot documentation specifies that a transition from LOCKED to UNLOCKED requires user confirmation and wipes data. citeturn0search1turn0search3

## iOS

Apple recovery/restore is supported through the documented recovery workflow. Restore can erase device data; Activation Lock and Apple Account protections are not bypassed. citeturn0search0turn0search11
