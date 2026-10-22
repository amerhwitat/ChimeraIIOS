# Cross-OS syscall and ABI implementation contract

## Isolation rule
Never dispatch a foreign OS syscall number directly to the Chimera kernel. Each ABI personality must validate execution mode, syscall number, argument widths, pointers, permissions and return/error conventions, then translate supported operations to internal services. Unknown calls return a documented not-supported error. Do not expose kernel entry points directly to untrusted processes.

## ABI profiles

| Personality | Entry and conventions | Required policy |
|---|---|---|
| Chimera native x86-64 | Versioned native syscall IDs and register layout defined by the authoritative Chimera ABI header | The only authoritative in-kernel ABI; never infer IDs from Linux, Darwin or Windows. |
| Linux x86-64 | `syscall`; number/result in RAX; args RDI, RSI, RDX, R10, R8, R9 | Dedicated Linux-number table, safe pointer/FD validation and Linux error semantics. |
| Linux i386 | Compatibility entry such as `int 0x80`, only if 32-bit process support exists | Separate 32-bit table and register validation; otherwise reject explicitly. |
| Darwin/macOS | Darwin BSD syscall class encoding and Mach traps are distinct namespaces | Keep Mach IPC/traps separate from BSD calls; version the supported ABI. |
| Windows NT | Win32 APIs are the app-facing boundary; raw SSNs vary by OS build | Do not hardcode SSNs or dispatch guessed `Nt*` numbers. Use a named API compatibility provider. |
| BSD/System V | Per-OS and per-version tables and conventions | FreeBSD, OpenBSD, NetBSD and Solaris are not one generic syscall ABI. |

Linux reference operations include read/write/open/close/mmap/brk/getpid/clone/execve/exit, but their Linux IDs are not Chimera native IDs. Darwin `mach_msg_trap` is distinct from BSD calls. Windows `NtCreateFile`, `NtReadFile`, `NtWriteFile`, `NtAllocateVirtualMemory`, `NtTerminateProcess` and `NtQuerySystemInformation` are named API contracts, not stable public SSN constants.

## Implementation and tests
- Define symbolic name, numeric ID, argument schema, privilege policy, error contract and tests for each native service.
- Generate IDs from one registry and reject duplicates.
- Verify ring-3 origin from the real trap frame; bind acknowledgements to actual PID and ABI personality. Never hardcode PID 1.
- Validate user pointers and lengths; guard integer overflow, mapping permissions and invalid handles.
- Test invalid IDs, malformed arguments, bad pointers, privilege violations, process exit and concurrent calls.
- Mark compatibility profiles `not implemented` until an actual adapter and executable tests exist.
- Candidate ELFs, successful compilation, catalog coverage and syscall stubs are not production readiness.
