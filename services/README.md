# Services compatibility tree

The JSON registry is canonical. Native adapters are intentionally thin: they expose capability mappings and return `unsupported` for operations that require privileged or platform-specific functionality not yet implemented. This keeps the service ABI testable and prevents compatibility code from silently bypassing Koronos security policy.

## Linux service management

The Ubuntu/Debian systemd adapter is documented in [LINUX_SERVICES.md](../docs/LINUX_SERVICES.md). Use `chimera-services list`, `status`, `install`, `profile`, and explicit `enable-now`/`disable-now` commands. Package installation does not automatically enable network listeners. The declarative catalog lives in `services/linux/service-catalog.json`.
