# Windows Compatibility and Clean-Room Integration

Chimera II OS provides Windows-compatible interfaces through documented/public contracts and independently implemented code.

## Allowed inputs

- public Microsoft API and ABI documentation
- PE/COFF specifications
- published Win32/NT interface behavior
- legally redistributable SDK/WDK components under their applicable terms
- clean-room compatibility tests

## Prohibited inputs

Do not copy, distribute, translate, or derive implementation code from leaked or unlawfully disclosed Microsoft Windows source. Microsoft has explicitly stated that the Windows 2000/Windows NT 4.0 source disclosed in 2004 was illegally posted and protected by copyright and trade-secret law.

If a Library artifact appears to contain leaked Windows source, it remains a quarantined research/provenance item and is not a build dependency or implementation source.

## Architecture

`integrations/windows/` should contain clean implementations of required compatibility interfaces, including:

- PE/COFF loading boundaries
- Win32 API shims
- synchronization primitives
- virtual memory semantics
- I/O control contracts
- KMDF-compatible driver interfaces where legally documented
- user-mode test harnesses

The implementation must remain independent from confidential Microsoft implementation details.
