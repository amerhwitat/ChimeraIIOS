# Chimera II OS Hardware Drivers

Chimera uses the Linux kernel driver model and ALSA for hardware access. ALSA automatically detects supported audio devices and creates /dev/snd/* devices; hardware-specific ALSA modules are maintained by the Linux kernel. citeturn0search1turn0search12

## Audio coverage

- Intel/AMD HDA controllers and HDMI/DisplayPort audio.
- Realtek, Conexant, Cirrus, Analog Devices and SigmaTel HDA codecs.
- NVIDIA/AMD GPU HDMI/DP audio.
- USB Audio Class devices through snd-usb-audio.
- Creative and other PCI sound cards where the corresponding in-tree ALSA module exists.
- Intel Sound Open Firmware (SOF) devices.
- AMD ACP audio devices.
- USB/MIDI professional audio devices.

The ALSA configuration documentation lists snd-usb-audio for USB audio/MIDI and the HDA driver/module families, and supports automatic module loading through kernel aliases. citeturn0search1

ASoC is used for SoC/embedded audio and separates codec, platform and machine drivers. citeturn0search5turn0search7

## Driver selection

Chimera selects, in order: in-tree kernel driver; Ubuntu-signed driver/userspace packages; signed Linux/SOF firmware; then signed fwupd firmware where supported.

It does not execute arbitrary vendor .run, PowerShell, shell, or downloaded kernel-module installers.

## Hardware detection

The Drivers panel runs PCI, USB, udev, DMI, DRM, ALSA, network, storage and firmware detection. Hardware state is recorded in /var/lib/chimera/drivers/state.json.

## Binary policy

Chimera packages distribution binaries and kernel modules needed for supported drivers into the ISO where practical. Proprietary vendor binaries are not copied into this source repository; supported vendor drivers are obtained at runtime only from authenticated package repositories.
