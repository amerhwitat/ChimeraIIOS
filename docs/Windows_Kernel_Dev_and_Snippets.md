# Windows Kernel Development and Chimera Integration Notes

## Scope

This is an isolated Windows kernel-development reference for the optional Chimera Windows integration. The Chimera core does not depend on WDK headers.

## Best practices

1. Target a documented Windows DDI and supported WDK version.
2. Prefer KMDF for new drivers unless a WDM design is specifically required.
3. Validate every IOCTL length and structure field before use.
4. Respect IRQL: pageable operations belong at PASSIVE_LEVEL; DPC/ISR paths must remain non-pageable and bounded.
5. Use WDF queues, DMA abstractions and framework lifetime management instead of hand-written resource ownership where possible.
6. Never expose raw physical addresses to user mode.
7. Use IOMMU-aware DMA APIs and unwind all partial allocations.
8. Apply quotas/timeouts to operations that can consume pinned memory or device resources.
9. Test with Driver Verifier, static analysis, fuzzing and kernel debugging.
10. Sign production drivers according to Microsoft's current driver-signing requirements.

## Minimal KMDF echo architecture

```text
User-mode test
      ↓ DeviceIoControl
KMDF I/O queue
      ↓ validate
Echo handler
      ↓ buffered copy
WdfRequestCompleteWithInformation
```

The sample in `integrations/windows/KMDF_ChmEcho/` is intentionally limited to a bounded buffered echo operation. It is not a DMA or page-pinning implementation.

## IRQL model

| Level | Typical work |
|---|---|
| PASSIVE_LEVEL | pageable code, file operations, most WDF configuration |
| DISPATCH_LEVEL | DPCs, short synchronization, non-pageable code |
| DIRQL | interrupt service routines; keep extremely short |

## Safe IOCTL pattern

Use `WdfRequestRetrieveInputBuffer` and `WdfRequestRetrieveOutputBuffer`, verify minimum and maximum lengths, calculate copy sizes without integer overflow, and complete the request exactly once.

## DPC/work-item pattern

A DPC should only perform bounded, non-blocking work. Queue longer or pageable work to a WDF work item, which runs at PASSIVE_LEVEL.

## DMA guidance

For real hardware integrations, use the WDF DMA enabler and Windows DMA APIs. Do not turn user virtual addresses into physical addresses and hand those values to devices. The device-visible mapping must be produced by the approved DMA/IOMMU path and released on every error path.

## Debugging

Recommended development loop:

1. Build with symbols.
2. Test in a VM or dedicated test machine.
3. Enable kernel debugging when diagnosing crashes.
4. Run Driver Verifier against the test driver.
5. Capture crash dumps and inspect stack/IRQL/resource state in WinDbg.
6. Fuzz IOCTL boundaries and malformed structures.

## Historical W2K-ASM material

`W2K-ASM.txt` is retained as historical source context. Its Microsoft Confidential/historical content is not copied into the Chimera source tree. The project only uses general, non-expressive engineering lessons such as source/assembly correlation, calling-convention awareness, symbolized debugging and portability concerns.

## Build isolation

The Windows sample is excluded from the portable CMake target. Build it with the Windows Driver Kit in a Windows development environment. This prevents WDK headers and libraries from affecting Linux/QEMU/host builds.
