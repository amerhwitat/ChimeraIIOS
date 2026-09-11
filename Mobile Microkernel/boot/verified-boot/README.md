# Verified Boot Adapter

This directory defines the interface between platform verified-boot infrastructure and the Mobile Microkernel.

The adapter receives an already-authenticated kernel image and normalized boot metadata. It must expose verification state and, where supported, measurement/rollback information.

No vendor bootloader binaries are redistributed here. Platform implementations are expected to bind this interface to their permitted firmware environment.
