# Windows / Linux / macOS Compatibility Gap Matrix

This matrix records implementation targets without claiming that proprietary operating-system source has been copied.

| Area | Windows reference pattern | Linux reference pattern | macOS reference pattern | Chimera target |
|---|---|---|---|---|
| AI | Windows ML / ONNX execution providers | accelerator/runtime ecosystem | Metal/Accelerate-style provider boundary | provider-neutral local inference |
| Async I/O | IOCP-style completion model | io_uring | dispatch/event-driven services | Kore + shared-ring IPC |
| Network acceleration | Winsock/RIO patterns | AF_XDP/eBPF | NetworkExtension/provider boundary | Spotnik zero-copy provider API |
| Security | capability/ACL/token/service boundaries | namespaces/capabilities/LSM/eBPF | entitlements/sandbox/code-signing | Aegis capabilities + signed services |
| Virtualization | Hyper-V style VM abstraction | KVM/QEMU ecosystem | Hypervisor/Virtualization frameworks | CEF + Koronos VM service |
| Configuration | Registry/hive model | sysfs/proc/config files | preferences/property-list model | Hive unified registry adapter |
| Graphics | DirectX/provider architecture | DRM/KMS/Vulkan/OpenGL | Metal/CoreGraphics | Aurora provider abstraction |
| Storage | NTFS/ReFS/storage stack | VFS + many filesystem implementations | APFS/HFS+ compatibility boundary | VFS/TensorFS + filesystem adapters |
| Service management | SCM | systemd/OpenRC/etc. | launchd | Kore service manager |
| IPC | ALPC/RPC patterns | pipes/sockets/shared memory | XPC/Mach-message patterns | capability IPC + shared rings |
| Observability | ETW/performance counters | tracepoints/eBPF/perf | unified logging/instruments boundary | deterministic tracing + metrics |

## Missing-work policy

Each row is an adapter/interface target. Native Chimera implementation is added only where specifications and licensing permit. Proprietary internals are represented by clean-room behavioral contracts, compatibility shims, or external provider adapters.
