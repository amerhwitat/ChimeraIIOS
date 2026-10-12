# Chimera II application programming models

Chimera exposes two source-level models over one capability-checked service boundary. They are **programming APIs**, not a promise that every foreign binary or kernel ABI is already implemented.

## Model A: event-driven desktop applications

Use `chimera/event.h` for a portable event loop and `chimera/win32_message.h` for a Win32-shaped message pump (`chm_win32_post_message`, `chm_win32_get_message`, `chm_win32_dispatch_message`). Events include window lifecycle, keyboard/pointer input, timers, file changes, I/O readiness, quit and application-defined events.

```c
#include "chimera/event.h"
#include <stdio.h>

static void on_event(const chm_event *e, void *context) {
    (void)context;
    if (e->type == CHM_EVENT_USER)
        printf("user event: %lld\n", (long long)e->value1);
}
int main(void) {
    chm_event_queue *q = chm_event_queue_create(64);
    if (!q) return 1;
    CHM_PostMessage(q, 1, CHM_EVENT_USER, 42, 0);
    CHM_PostMessage(q, 1, CHM_EVENT_QUIT, 0, 0);
    int rc = chm_event_run(q, on_event, NULL, 10);
    chm_event_queue_destroy(q);
    return rc;
}
```

The SDK's `CHM_*` and `chm_win32_*` functions are a clean-room compatibility surface; they are **not** aliases for Microsoft's proprietary implementation. The current queue is a thread-safe user-space queue suitable for hosted SDK programs. A native Koronos GUI server still needs to feed input/window/timer notifications through a capability-checked kernel IPC backend.

Windows source ports can map familiar concepts as follows:

| Windows concept | Chimera SDK equivalent | Scope |
|---|---|---|
| `MSG`, `GetMessage` | `CHM_MSG`, `CHM_GetMessage` | implemented user-space queue |
| `PostMessage` | `CHM_PostMessage` | implemented user-space queue |
| `DispatchMessage` | `CHM_DispatchMessage` | callback dispatch |
| `CreateWindowEx`, HWND | Aurora window-service API | separate backend; not supplied by this queue |
| kernel APC/DPC, hardware IRQ | kernel interrupt/scheduler/IPC services | kernel-only; not callable as ordinary app functions |

## Model B: file-oriented POSIX/Linux/macOS applications

Use `chimera/file.h` for descriptor-style `open/read/write/close/unlink` source ports. It deliberately follows the common POSIX shape so command-line tools and file filters can share a portable programming model.

```c
#include "chimera/file.h"
#include <string.h>
int main(void) {
    const char data[] = "hello from a file-oriented program\n";
    chm_fd fd = chm_open("hello.txt", CHM_O_WRITE_ONLY | CHM_O_CREATE, 0600);
    if (fd < 0) return 1;
    int64_t n = chm_write(fd, data, sizeof(data)-1);
    int close_rc = chm_close(fd);
    return n == (int64_t)(sizeof(data)-1) && close_rc == 0 ? 0 : 2;
}
```

Hosted SDK builds forward to the host C runtime. On native Chimera, these calls must be connected to the kernel's validated VFS/file-handle services; the adapter does not currently pretend that the kernel's `CHM_SYS_READ/WRITE` cases are fully implemented.

## Syscalls, interrupts and privilege boundaries

- Applications call stable Chimera library APIs. The library marshals a request to the kernel syscall/service boundary.
- The kernel validates the process, capabilities, handles, user pointers, buffer lengths and access rights before performing an operation.
- Hardware interrupts are delivered to kernel interrupt handlers. User applications receive events/IPC notifications, not raw IRQ control.
- Linux `syscall`/`int 0x80`, Darwin/Mach traps, and Windows NT syscall conventions are ABI-specific entry mechanisms. Compatibility code translates their documented arguments into canonical Chimera service requests; it must not assume the syscall numbers are interchangeable.
- The current kernel dispatcher has a small implemented subset (PID placeholder, yield, timer ticks, and exit acknowledgements). Several other canonical IDs return `ENOSYS`. Windows interrupt vectors and foreign syscall identities can be recognized as metadata, but recognition is not equivalent to a complete Win32, Linux or Darwin implementation.
- Kernel-only operations, device access and driver loading require capabilities and a validated native service implementation. Never invoke `sti/cli`, write IDT entries, or access devices from ordinary applications.

## Objective-C and macOS source

`sdk/bin/chimera-objc` invokes Clang in Objective-C mode:

```sh
# Compile a portable Objective-C translation unit for the current host:
sdk/bin/chimera-objc -c hello.m -o hello.o

# Cross-compile an object for Intel macOS (does not require an Apple SDK):
sdk/bin/chimera-objc --chimera-target=darwin-x86_64 -c hello.m -o hello.o

# Apple Silicon macOS object:
sdk/bin/chimera-objc --chimera-target=darwin-arm64 -c hello.m -o hello-arm64.o
```

Set `CHIMERA_OBJC_COMPILER` to a Clang executable. To link a macOS application, supply a matching, legally obtained macOS SDK through `CHIMERA_MACOS_SDK`; compiling an object is not the same as producing a runnable `.app`. Foundation/AppKit frameworks, Apple Objective-C runtime behavior, code signing, bundle layout and Darwin syscalls need the corresponding SDK/runtime. Chimera does not bundle Apple proprietary frameworks or claim that arbitrary macOS binaries run natively on Koronos.

## Status vocabulary

- **Implemented and tested here:** SDK queue, callback dispatch, hosted POSIX-shaped file adapter, Clang Objective-C driver argument handling.
- **Requires a native backend:** kernel VFS syscall implementation, Aurora window server, event-to-input IPC, timer/file-watch notifications.
- **Compatibility target, not completed:** full Win32 user32/kernel32, Linux/POSIX syscall coverage, Darwin/Mach system calls, Windows PE/macOS Mach-O execution across architectures.

The native SDK is intended to make the two programming styles understandable and incrementally runnable without disguising missing kernel, framework or ABI work as completed support.
