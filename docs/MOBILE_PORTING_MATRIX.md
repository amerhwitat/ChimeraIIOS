# Mobile porting matrix

| Class | Initial status | Required validation |
|---|---|---|
| Reference AArch64 | research scaffold | boot handoff, MMU, storage, display |
| Qualcomm generic | profile template | exact SoC/model, GKI/KMI, vendor modules, AVB |
| MediaTek generic | profile template | exact SoC/model, vendor boot protocol, modules, AVB |
| Samsung generic | profile template | exact model, SoC, bootloader policy, vendor modules |
| Other Chinese OEMs | profile template by SoC | exact model, boot chain, partition map, vendor modules |

A profile is not promoted to supported status until a reproducible image has booted on the exact model and passed storage, display, input, networking, power, recovery and verified-boot tests.
