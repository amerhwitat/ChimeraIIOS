# Chimera II Web UI Integration

Canonical Web UI/OS source-of-truth. The `amerhwitat/test` repository is the integration and conformance hub.

## Shared surfaces
- Aurora Three.js/WebGL Glass Desktop
- Linux desktop profile adapters
- Windows desktop profile adapters
- Unified terminal/help (`man`, `apropos`, `whatis`, `info`, `help`)
- C/C++/GCC/g++ and Chimera CISC/RISC tooling surfaces
- CPU4096/ISA visualization adapters

## Boundary
WebGL is presentation-only. Browser code does not receive arbitrary host shell, filesystem, credentials, or native desktop access. Native Linux/Windows sessions require an explicitly authorized adapter.

## Compatibility
Existing ABI, command catalog, man catalog, and desktop contracts remain compatible; the Web UI consumes versioned manifests and migrates existing catalogs rather than replacing them.
