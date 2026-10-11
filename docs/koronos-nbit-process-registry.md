# Koronos process-mode registry and cross-width IPC

Koronos records execution-mode metadata for processes admitted through the transactional ELF loader and exposes a bounded registry API for other compatibility loaders to register/update/unregister their process contexts.

## Registry APIs

- `chimera_nbit_process_init`: register or update a process ID, N-bit mode, and compatibility target.
- `chimera_nbit_process_get`: query one registered context.
- `chimera_nbit_process_snapshot`: copy up to the requested number of contexts into caller-owned memory. Pass a capacity of `CHIMERA_NBIT_MAX_PROCESS_MODES` to retrieve the full registry.
- `chimera_nbit_registry_get_snapshot`: report current count and registry capacity.
- `chimera_nbit_process_set_mode` / `chimera_nbit_process_set_compatibility`: update metadata when a process changes execution mode or compatibility personality.
- `chimera_nbit_process_unregister`: remove a context when the process exits or its handoff fails.

The kernel monitor prints the total registered count and a small sample to avoid flooding the early VGA console; the snapshot API is the full inventory interface. Scheduler callbacks and process contexts are distinct concepts: registering a mode context does not itself create a scheduler task.

## Cross-width IPC contract

Processes with different N-bit modes communicate through a canonical byte-stream envelope. The sender and receiver mode widths are metadata, not a requirement that the two sides share pointer size or native register layout. `chimera_nbit_ipc_prepare` resolves both registered process contexts and constructs an envelope with a bounded, exact payload byte count. `chimera_nbit_ipc_validate` rejects invalid modes, missing payloads, oversized messages, and inconsistent bit/byte lengths. `chimera_nbit_ipc_copy_payload` copies the payload into a receiver-owned buffer and rejects insufficient capacity.

**Security boundary:** the envelope's payload pointer is a kernel-side source pointer for the bridge to copy from. It must never be interpreted as a valid pointer in the receiver's address space. A production IPC transport still needs the syscall/endpoint authorization layer, address-space-aware copy-in/copy-out, queueing, cancellation, and lifetime management; this API provides the mode registry and safe copy primitive, not a complete message broker.

## Current execution limits

The current generic ELF loader accepts the existing ELF64 load-plan format and registers it as a 64-bit process before user handoff. Other architecture/compatibility loaders should register their own bitness and compatibility target with the same registry. A 128–8192-bit mode is currently an execution/emulation profile, not proof of native hardware support or a real wider-instruction execution engine. The registry does not claim to enumerate processes launched outside loaders that use this API.
