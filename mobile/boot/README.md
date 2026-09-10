# Spit Fire Mobile boot integration

Spit Fire Mobile is a boot-handoff layer, not a universal OEM bootloader replacement. Each profile records the boot protocol and partition constraints. On Android-class devices, the implementation must coexist with the device's ROM/OEM boot chain and verified-boot policy.

Supported research paths:
- fastboot / fastbootd
- documented vendor recovery handoff
- reference-board boot flow

Production support requires exact device testing and authorized bootloader unlock/signing procedures.
