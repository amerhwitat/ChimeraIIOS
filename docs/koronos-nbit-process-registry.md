# Koronos process-mode registry and cross-width IPC

## Process visibility and execution modes

Every process admitted through `chimera_process_admit_elf` is registered in the kernel-wide N-bit registry as a 64-bit ELF process. Launchers that select a compatibility personality or an emulated mode must call `chimera_process_set_execution_mode(pid, bits, compatibility_target)` before making the process runnable. Launchers that do not use the common process table must register directly through `chimera_nbit_process_init`. A registry snapshot reports process-mode metadata; it is not a substitute for the scheduler's task inventory.

Process exit and fault transitions retire the mode record and ask the IPC service to discard the process's queued messages and endpoints. Failed admission/loading rolls back its registration. The registry has a fixed capacity of `CHIMERA_NBIT_MAX_PROCESS_MODES` (1024); a registration failure must be treated as launch failure, not silently ignored.

## Capability-based IPC service

`kernel/core/ipc.cpp` implements bounded endpoint queues with endpoint capability checks, per-message sender/receiver mode metadata, FIFO delivery, explicit cancellation, and process-exit cleanup. Queue depth is 16 messages per endpoint and payload size is limited to 1024 bytes. A sender's user pointer is copied into a kernel-owned staging buffer by the configured `copy_from_user` callback before enqueue. Receive copies from the kernel-owned queue through `copy_to_user`; the receiver never dereferences a sender address. The callbacks must perform real address-space validation and fault-safe copy operations in the platform/syscall layer. The `out` message-info structure is a kernel-owned output parameter.

An endpoint capability is a bearer secret: a trusted kernel/service caller must mint and distribute an unpredictable 64-bit capability, keep it out of untrusted logs, and revoke it by unbinding the endpoint. This module checks the capability but does not itself provide a cryptographic random-number generator or user-facing syscall dispatcher. Calls to initialize the service must provide valid copy callbacks before IPC is enabled.

## Cross-width contract and physical hardware

IPC transports canonical bytes; sender and receiver mode widths are metadata and are never interpreted as shared pointer widths or register layouts. The N-bit profile distinguishes `native_nbit_mode` from `maximum_emulated_nbit`. On a typical x86-64 CPU, 64 bits is the native general-purpose execution width; 128–8192-bit profiles are emulation targets unless a hardware backend explicitly proves otherwise. Vector extensions such as AVX-512 do not turn the CPU's general-purpose execution mode into a native 512-bit process ABI. Generated N-bit ELF notes are build artifacts, not evidence of native instruction execution.

## Acceptance boundary

Host regressions cover process-mode registry operations, IPC authorization, bounded queues, cross-width delivery, cancellation, and cleanup. The freestanding kernel build and QEMU boot smoke test remain required; they must pass on the latest commit before the work is considered verified. Full process visibility also depends on every out-of-tree or independent compatibility launcher registering with the common API. The current generic ELF load-plan path remains ELF64-only; this change does not implement ELF32, Windows/Linux syscall translation, a complete user syscall dispatcher, or a physical wider-than-64-bit instruction engine.
