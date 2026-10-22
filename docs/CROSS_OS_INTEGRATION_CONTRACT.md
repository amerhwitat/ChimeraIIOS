# Cross-OS applications, settings, drivers, and CPU compatibility

This contract is shared by ChimeraIIOS and OctavianOS. It is an integration boundary and inventory schema, not a claim that every listed external application, OS ABI, device, or setting is already implemented.

## Application intake

Use the existing open-source software catalog as an intake source, then add each application with: stable ID, license, upstream URL, supported CPU architectures, source/binary format, dependencies, native package/build recipe, runtime permissions, security posture, and test evidence. Track each target separately as `native_verified`, `native_candidate`, `compatibility_provider_required`, `emulated`, `unsupported`, or `not_tested`. Do not label a catalog entry as installed, executable, or compatible without a working package/runtime provider and test evidence.

Target families to inventory include Linux, Windows, and macOS, plus native ChimeraIIOS and OctavianOS applications. Compatibility must consider ABI, executable format, syscalls, libraries/frameworks, signing/notarization, graphics/audio, device access, and licensing—not just CPU instruction compatibility.

## Settings and Control Panel

The control-panel registry provides common cross-platform sections and stable setting IDs. Each OS adapter must expose only settings it can read, validate, apply, verify, and roll back. Unsupported controls stay visible but disabled with a reason. Sensitive data and machine identifiers must not be exported by default.

## Hardware and driver assistant

The RNN/LLM is an advisory classifier and ranking layer over deterministic hardware inventory and a signed driver catalog. It may recommend or scaffold code for review; it must not generate and load kernel drivers autonomously. A candidate driver must pass architecture/ABI checks, signature and license checks, bounded probe, rollback tests, and functional/error-path tests before it can be marked `bound_verified`.

Inventory should capture PCI/USB IDs, ACPI identifiers, firmware/SMBIOS details, CPU feature bits, bus topology, and resource windows while minimizing exposure of serial numbers and MAC addresses. Keep local inventory local by default. Confidence scores rank candidates; they do not replace evidence.

## CPU and operating-system compatibility

Detect actual CPU features at runtime and identify executable format, OS ABI, syscall convention, memory model, and required instructions before selecting native execution or a compatibility provider. Do not infer support for Windows or macOS binaries from POSIX compatibility. The x86_64 native target remains the only production candidate until architecture-specific build and boot evidence exists. Other CPU families require porting or emulation evidence. Configurable 128–8192-bit research profiles are software-defined/emulated modes, not claims of physical CPUs.

## Required gates before enabling or publishing

1. Schema validation and duplicate-ID checks.
2. OS adapter tests for capability detection, apply/verify/rollback, and permissions.
3. Driver inventory/match tests using known and unknown IDs, signed/unsigned catalogs, and malformed records.
4. No model-originated code may be loaded without normal review, signing, and tests.
5. Native/compatibility/emulation states remain distinct in UI and reports.
6. Preserve the existing production release gate: Live/Installer/Recovery × BIOS/UEFI, real target operation, user-originated readiness, Aurora/session handoff, storage persistence, and genuine AP-backed SMP must all be independently proven.
