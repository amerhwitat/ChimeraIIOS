# Chimera II hardware-aware N-bit runtime

Koronos now exposes a hardware profile and an N-bit execution policy.

- The hardware probe identifies the host architecture, pointer width, CPU count and selected instruction features.
- The default mode is chosen from the native execution width; larger modes are represented through the Chimera emulation/execution layer.
- N-bit mode is a **process property**. Changing the desktop default affects new processes; it does not silently rewrite an existing process address space or ABI.
- IPC is width-neutral: messages carry sender/receiver widths and a bounded payload, allowing 8/16/32/64/128/256/512/1024/2048/4096/8192-bit processes to communicate through one canonical transport.
- Compatibility targets are explicit (native, Windows, Linux, BSD, Darwin, Android, iOS) and are implemented above the native Koronos scheduler/kernel.

This keeps the kernel ABI stable while allowing heterogeneous execution modes.
