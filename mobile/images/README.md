# Mobile image outputs

`build-mobile-image.sh` currently creates a validated research-image layout containing the exact device profile.

A production flashable image additionally requires:
- exact device kernel/GKI/KMI compatibility
- device vendor modules
- partition-specific image construction
- authorized AVB signing
- rollback metadata
- device bootloader/recovery integration

Those inputs are intentionally not guessed or generated from a generic phone profile.
