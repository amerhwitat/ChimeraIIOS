# Windows / Linux / Unix Driver Integration

## Windows

Chimera II provides a user-space adapter boundary for Windows Driver Model / WDK concepts. Real WDM/KMDF/UMDF binaries are not copied into this repository. A future native port can implement the same capability interface and keep Microsoft/vendor licensing intact.

## Linux

Linux-native adapters map to the kernel's device model and common subsystems such as DRM/KMS (GPU/display), ALSA (audio), V4L2 (camera), networking, USB, PCI, NVMe and input/HID. Chimera's driver registry records the capability and expected stack; kernel integration belongs in the target-specific port.

## Unix-like systems

The same capability layer can host BSD/macOS adapters. Audio uses CoreAudio/AVFoundation boundaries on Apple platforms; graphics can use Metal or OpenGL compatibility where appropriate.

## Safety

No unsigned kernel module is loaded by the registry. Driver loading must pass architecture, ABI, signature/policy and device-match checks. User-space providers are preferred for experimental features.
