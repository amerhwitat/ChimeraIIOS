# Mobile Platform Contract

The Mobile Microkernel uses a narrow architecture-neutral contract between the privileged core and AArch64/RISC-V64 platform backends.

## Contract

`include/chimera/mobile/platform.hpp` defines:

- `MobileArchitecture` — AArch64 and RISC-V64 target identities.
- page-size metadata;
- online CPU-count metadata;
- minimum-memory validation;
- a small validity predicate suitable for boot-time validation.

The contract is metadata-only. It does not access host physical addresses and does not assume a particular SoC.

## Architecture boundaries

- `arch/arm64/exception_vectors.S` is an ABI integration point for future AArch64 exception-vector code.
- `arch/riscv64/trap_entry.S` is an ABI integration point for future RISC-V64 trap handling.
- GIC, interrupt-controller, timer, MMU/page-table, cache, CPU hotplug, PSCI/SBI and board-specific initialization must remain in platform backends.

## Validation

The host-side `platform_contract` test validates the architecture-neutral metadata contract. It is not a substitute for target-hardware validation.

## Security boundary

Platform code must treat firmware/device-tree/ACPI data as untrusted input, validate lengths and ranges, and avoid dereferencing arbitrary physical addresses. Privileged services should receive capabilities rather than raw device authority.
