# Mobile IPC

IPC is capability controlled and designed for low-copy mobile service communication.

Message metadata contains sender, receiver, capability and sequence information. Higher-level transports can add shared-memory rings for large buffers while retaining explicit ownership and lifetime rules.

The trusted-node fabric must remain outside the privileged kernel. Node discovery, cryptographic identity, synchronization and model exchange are userspace services governed by the repository's trusted-node policy.
