# Services compatibility tree

The JSON registry is canonical. Native adapters are intentionally thin: they expose capability mappings and return `unsupported` for operations that require privileged or platform-specific functionality not yet implemented. This keeps the service ABI testable and prevents compatibility code from silently bypassing Koronos security policy.
