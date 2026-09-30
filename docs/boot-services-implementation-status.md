# Native Boot and Enterprise Services Implementation Status

## Implemented

- Shared service registry, profiles, hardware requirements, security policy and dependency graph under `config/services/`.
- Native freestanding Kore service ABI and deterministic dependency resolver in `kernel/include/chimera/service.h` and `kernel/core/service.cpp`.
- Koronos build integration and required-symbol validation for Kore.
- Koronos bootstrap registration of core Kore services.
- Jasper/GRUB boot-mode registry covering Normal, Recovery, Safe Mode, Last Known Good, Live Aurora, Installer, Diagnostics and chain-loader.
- Measured/trusted boot policy contract with TPM capability gating.
- Installer enterprise-service selection metadata and dependency-expansion utilities.
- Aurora Service Center contract and Kore-only privileged mutation boundary.
- Local validation harness and GitHub Actions workflow definition.

## Pending target-environment verification

- Actual local Koronos compilation on the user's WSL/host.
- QEMU/physical boot validation for each boot mode.
- Full Aurora GUI wiring to the existing desktop implementation.
- Final ISO builder staging of authoritative `config/services` into the installed root filesystem; the existing builder already stages the `services/` and `installer/` trees, while installation materialization is provided by `installer/services/apply_service_plan.py`.
- Secure Boot/TPM measurement validation on hardware that exposes those facilities.

These items are deliberately marked pending rather than claimed as successful until the target environment produces the corresponding build/boot evidence.
