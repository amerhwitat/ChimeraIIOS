# Hyper-V support

Chimera II OS targets Hyper-V Generation 2 for the UEFI path. The helper creates a Gen-2 VM, attaches the ISO as virtual DVD, uses VHDX storage, configures the UEFI boot order, and uses the Microsoft UEFI CA Secure Boot template by default. Use -DisableSecureBoot when testing unsigned/custom boot binaries.

Hyper-V provides virtual firmware and devices to the guest; host physical hardware is not automatically passed through. Explicit DDA/USB/network configuration remains host-specific.
