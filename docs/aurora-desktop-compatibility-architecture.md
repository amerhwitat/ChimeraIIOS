# Aurora Desktop Compatibility Architecture

## Scope

Aurora is a native Chimera desktop shell. This specification defines a Windows-like desktop interaction model without copying proprietary operating-system implementation, binaries, icons, fonts, sounds, or artwork.

## Event pipeline

`hardware -> input driver -> Aurora event queue -> hit test -> window/widget -> application`

Every event carries a monotonically increasing sequence number, timestamp/tick, device id, modifiers, pointer coordinates when applicable, target window id, and propagation flags.

## Core event families

- pointer: move, enter, leave, down, up, click, double-click, context-click, middle-click, wheel, horizontal-wheel, drag-start, drag-over, drop, capture-lost
- keyboard: key-down, key-up, text-input, shortcut, accelerator
- window: create, destroy, show, hide, focus, activate, deactivate, move, resize, minimize, maximize, restore, close, paint, expose
- shell: desktop-click, desktop-context-menu, icon-select, icon-open, icon-arrange, desktop-zoom, taskbar-action, menu-open, menu-select
- filesystem: select, open, rename, copy, cut, paste, delete, properties, preview, thumbnail-ready, association-changed
- clipboard: offer, request, data, ownership-lost
- drag/drop: enter, motion, accept, reject, leave, drop
- application: launch, suspend, resume, terminate, crash, permission-request
- device: connect, disconnect, display-change, audio-change, input-change

## Mouse semantics

Single click selects. Double click opens the selected object using its association. Right click opens a context menu for the hit-tested object. Middle click is available to applications and may be configured for shell actions. Drag begins after a configurable motion threshold while a button is held.

Double-click timing and distance are user-configurable. Pointer capture is mandatory for reliable drag/resize operations.

## Keyboard semantics

The compatibility keymap provides configurable mappings for common desktop accelerators: Alt+Tab, Alt+F4, Alt+Space, Super/Win shell actions, Ctrl+C/X/V/Z/A, F2 rename, F5 refresh, Delete, Shift+Delete, Enter, Space, Escape, navigation keys, and Ctrl+mouse-wheel zoom. Native Aurora bindings can coexist and take precedence according to the active keymap profile.

## File associations

Associations match extension, MIME type, content signature, URI scheme, executable format, and directory type. Each association points to a registered application/runtime plus an optional verb such as open, edit, preview, print, or run. User overrides take precedence over system defaults.

## Preview providers

Preview providers are sandboxed and asynchronous. Supported provider classes include images, PDF/document pages, text, audio metadata/artwork, video frames, archives, 3D models, and executable metadata/icons. A failed preview must never terminate the shell.

## Desktop zoom and views

Desktop and file-manager zoom are independent. Supported semantic levels are small, medium, large, extra-large, and custom. Ctrl+wheel, Ctrl+Plus, Ctrl+Minus, and Ctrl+0 are configurable defaults.

## Windows 3.1 / DOS compatibility

Windows 3.1 is an emulator/permissive-OS target shown under `Aurora -> Emulators -> Permissive OS`. It is not a preemptive native Chimera process environment.

DOS executables run in an isolated DOS compatibility runtime and receive a virtual memory/device model. Legacy programs that write directly to historical memory-mapped device areas are redirected to virtual devices; they cannot write arbitrary physical Chimera kernel memory.

## Windows generations

Compatibility profiles cover DOS, Windows 3.x, Windows 9x, Windows NT-family applications, and later PE applications where the corresponding runtime exists. User-supplied Microsoft installation media/components remain user-provided; Chimera does not redistribute proprietary Microsoft binaries.

## Audio and themes

Desktop sound events are represented by semantic ids such as `window.open`, `window.close`, `notification`, `error`, `device.connect`, `device.disconnect`, `file.copy`, `file.delete`, `menu.open`, `menu.select`, `login`, and `shutdown`. Theme packages can provide original or properly licensed recordings. Windows/macOS/Linux recordings are not bundled unless their redistribution rights are established.

## Security

Shell extensions, previewers, file handlers, compatibility runtimes, and emulator processes execute with least privilege. Untrusted previews and legacy runtimes are isolated from the kernel and native desktop state.

## Acceptance criteria

The contract is satisfied when Aurora can dispatch the event families above, register file associations, provide asynchronous previews, expose configurable keyboard/mouse behavior, provide desktop/file-manager zoom, host compatibility windows, and isolate legacy DOS/Windows runtimes from native kernel memory.
