# Chimera II Java Driver Layer

The `java/` tree provides the portable Java representation of Chimera II hardware and driver acquisition contracts.

## Packages

- `chimera.drivers.hardware` — normalized PCI/USB/device identifiers.
- `chimera.drivers.acquisition` — artifact metadata, policy, SHA-256 verification, matching and staging.

The Java acquisition manager is deliberately independent of kernel loading. It can be used by Aurora/UI tooling, diagnostics, package management and research services without granting the Java runtime kernel-driver privileges.

## Security model

1. HTTPS source.
2. Curated host allowlist.
3. Hardware-ID match.
4. SHA-256 verification.
5. Signature/trust policy.
6. License/provenance metadata.
7. Quarantine/staging.
8. Explicit platform installation step.

Build example:

```text
javac -d build $(find java/chimera -name '*.java')
java -cp build chimera.drivers.acquisition.DriverAcquisitionManagerTest
```

The Java implementation follows the same contracts as `drivers/python/driver_acquisition.py` and the C ABI in `drivers/c/chm_driver_acquisition.h`.
