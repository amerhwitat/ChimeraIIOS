# Chimera II Mobile Editions

Chimera II Mobile now has two complementary product modes for Android and Apple mobile platforms.

## Hosted Mobile Edition

Runs **on top of** the vendor operating system.

### Android

- APK/AAB packaging
- Kotlin/Java/C++ application layer
- Android NDK/JNI integration
- Binder/Intent/service boundaries
- Aurora mobile shell
- Koronos hosted runtime
- Spotnik application networking
- Nucleus/Hive/Kore/Aegis services

Android is a Linux-based software stack with a Linux kernel, hardware-abstraction layer and Android Runtime. The hosted edition therefore uses Android's supported application and native interfaces rather than attempting to replace the Android kernel from inside an ordinary application.

### iOS/iPadOS

- Swift/Objective-C/C++ application layer
- UIKit/SwiftUI
- Metal
- Foundation/CoreFoundation
- Keychain and system security boundaries
- TestFlight/development/App Store distribution as applicable
- Aurora mobile shell and Koronos hosted runtime

Apple's application sandbox and code-signing/distribution rules constrain what a normal iOS application can do. The hosted edition is designed around those APIs rather than requiring kernel access.

## BareMetal Mobile Edition

Boots directly on supported hardware through a device-specific boot path.

### Android hardware

The primary strategy is device profiling around AArch64 and, where applicable, Android GKI/KMI, vendor modules, device tree, AVB, A/B or dynamic partitions, recovery and rollback.

Android Generic System Images demonstrate that broad device compatibility is possible on compliant Treble devices, but Chimera bare-metal support still requires its own kernel, drivers and hardware profile. Android documentation states that GSIs require an unlocked bootloader and Treble compliance, among other requirements, and warns that unsuitable flashing can leave a device non-bootable.

### Apple mobile hardware

Bare-metal support is deliberately **not** described as universal flashing of every iPhone/iPad. Apple's secure boot chain verifies signed boot components beginning from immutable Boot ROM. Therefore Chimera can only provide a bare-metal Apple target where a lawful and technically available alternative boot path and sufficient hardware interfaces exist.

## Device coverage

The `mobile/device_matrix.json` registry covers Android, iOS/iPadOS and additional mobile OS families. It uses manufacturer/model/SoC/ISA/GPU/display/storage/boot/security/driver capabilities rather than claiming that one binary supports every handset.

Current target families include Pixel, Samsung Galaxy, OnePlus, Xiaomi/Redmi/POCO, Motorola, Sony Xperia, ASUS, Nothing, Huawei, Honor, Oppo, Realme, Vivo, Lenovo, Nokia, Fairphone, Android tablets and development boards, plus iPhone/iPad device generations and other mobile operating systems where adapters are technically available.

## Safety

Never flash a generic Chimera image solely because the CPU is ARM64. The hardware profile must validate the boot chain, partition layout, display, input, storage, networking, firmware, security state and recovery path first.
