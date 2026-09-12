# Chimera II Driver Acquisition

Chimera II OS can discover candidate Linux and Windows driver packages and acquire them into a quarantined staging area. Acquisition is deliberately separate from installation.

## Flow

```text
hardware probe
    -> hardware ID normalization
    -> source discovery
    -> compatibility ranking
    -> HTTPS acquisition
    -> SHA-256 verification
    -> signature/trust validation
    -> SPDX/license + provenance validation
    -> quarantine/staging
    -> explicit installation approval
    -> platform-specific driver loader
```

## Linux

Linux kernel modules are not assumed to be binary-compatible with Koronos. A `.ko` is accepted only when its declared kernel ABI matches the Chimera ABI policy. Otherwise Chimera acquires source or package metadata and routes it through the Chimera driver-port/adaptation layer.

This matters because Linux's in-kernel interfaces are not a stable binary interface for arbitrary external kernels. Linux source is also governed by its licensing/provenance rules; imported source must retain its original SPDX/license metadata.

## Windows

Windows driver packages are modeled as INF/CAT/SYS bundles. Chimera validates package metadata and signatures before staging. When running on Windows, final installation is delegated to the Windows Driver Store/SetupAPI mechanisms rather than bypassing Windows security.

Microsoft documents that Windows stages trusted driver packages in the Driver Store and validates the package/catalog signature before installation. Chimera therefore never disables signature enforcement as an acquisition strategy.

## Source policy

Default sources are curated in `drivers/acquisition_sources.json`. Network acquisition is not performed by the registry generator. Every acquired artifact must carry a cryptographic digest and provenance record.

## Security rules

- HTTPS only.
- Source allowlist.
- SHA-256 verification.
- Signature/trust policy.
- Hardware-ID and architecture matching.
- No automatic kernel loading.
- No Secure Boot/test-signing bypass.
- No proprietary redistribution unless its license explicitly permits it.
- Downloaded code remains inert until the installation policy authorizes it.

## References

- Linux kernel licensing rules: https://docs.kernel.org/process/license-rules.html
- Linux kernel source: https://github.com/torvalds/linux
- Microsoft Driver Store: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/driver-store
- Microsoft driver package selection: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/how-windows-selects-a-driver-for-a-device
