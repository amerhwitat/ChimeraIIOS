# Koronos Mobile architecture

Koronos Mobile is a separate target of the Chimera II microkernel family. It is not a universal replacement boot image for every Android handset.

## Boot chain

```text
SoC ROM / OEM boot chain
  -> unlocked or authorized bootloader
  -> Spit Fire Mobile / compatible handoff
  -> Koronos Mobile image
  -> device-specific vendor modules
  -> storage/display/input/radio services
  -> Aurora Mobile
```

Android's modern kernel architecture separates the generic kernel from hardware-specific vendor modules through GKI/KMI. Chimera follows that separation rather than copying vendor drivers into one generic image.

## Security

AVB, rollback protection, partition verification and device unlock state are part of each profile. Signing keys are never committed to the public repository.

## Porting rule

A handset is supported only after its exact model, SoC, boot protocol, partition map, display/GPU, storage, modem and vendor-module requirements have been tested. A generic Samsung, Qualcomm or MediaTek profile is a template, not a claim of compatibility.
