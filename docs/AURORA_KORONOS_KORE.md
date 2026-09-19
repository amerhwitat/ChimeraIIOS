# Aurora + Koronos + Kore integration

This phase connects the three layers without collapsing their trust boundaries.

Aurora is the user-facing Settings and hardware-management surface. Kore is the service lifecycle/dependency orchestrator. Koronos and Aegis enforce privileged-operation policy.

## Runtime path

Host hardware -> Aurora scanner -> hardware identity -> driver resolver -> provenance/signature/hash/license checks -> quarantine/stage -> explicit approval -> native or compatibility adapter -> health test -> rollback.

Service path:
Koronos -> Spotnik/Aegis/Nucleus -> Aurora -> driver-manager.

## Platform boundaries

Linux may use native signed Chimera drivers where the ABI is explicitly supported. Windows and macOS kernel drivers remain native-platform responsibilities and are exposed to Chimera through compatibility, virtualization, Wine/WSL, or virtual-device adapters. This prevents foreign kernel binaries from entering Koronos directly.

## Recursive discovery

Recursive web discovery is intentionally bounded by source policy and depth. It follows declared official vendor/OS/upstream sources and records provenance. It does not execute arbitrary scripts or treat a search result as trusted software.

## Settings

desktop/aurora/settings_schema.json provides the Windows-style category hierarchy requested for Aurora. Devices includes Drivers and Hardware, while Privacy & Security includes Updates and Drivers.

## Validation

Run:
python -m pytest drivers/tests system/kore/test_service_orchestrator.py

Run:
python3 system/kore/service_orchestrator.py plan
