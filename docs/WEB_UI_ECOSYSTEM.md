# Chimera II Web UI Ecosystem

This repository is the canonical Chimera II OS implementation/source-of-truth for the Web UI desktop architecture.

The ecosystem includes the Aurora Wayland Glass Desktop presentation, Three.js/WebGL desktop surface, unified terminal/help subsystem, Linux desktop profile adapters, Windows desktop profile adapters, C/C++ IDE/compiler surfaces, Chimera II ISA/CPU visualization, and secure native/VM adapter boundaries.

`amerhwitat/test` is the Web UI integration/conformance surface. Changes originating here should preserve this repository's canonical contracts.

Security: browser code is sandboxed and must not receive arbitrary host shell, filesystem, credentials, private keys, network, or native desktop-session access. Real Linux/Windows sessions require an explicitly authorized backend.
