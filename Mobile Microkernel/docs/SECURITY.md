# Mobile Security Model

The Mobile Microkernel uses a least-privilege, capability-oriented security boundary.

## Boot

The intended chain is hardware/ROM -> platform boot firmware -> verified boot metadata -> Mobile Microkernel -> signed system services. Platform implementations may integrate AVB-like verification, measured boot, secure storage and rollback protection.

## Kernel policy

- no arbitrary remote code execution through the trusted-node fabric;
- no unsigned kernel-module loading;
- driver access requires explicit capabilities;
- IPC endpoints validate capability and message metadata;
- debugging interfaces are disabled or explicitly authorized in production configurations;
- cryptographic keys remain behind hardware/platform key services where available.

Security-sensitive platform code must be reviewed separately from portable kernel code.
