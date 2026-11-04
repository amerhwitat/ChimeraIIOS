# Chimera Aurora / Marine native desktop interaction contract

## GTK4 shell behavior

The host Linux GTK4 shell exposes File, Edit, View, Window and Help menus. Application cards support single-click selection, double-click launch, triple-click Properties and a right-click context menu with Open, Rename and Properties. The card Open button remains keyboard accessible.

The main workspace is hosted in a GTK scrolled window with automatic horizontal and vertical scrollbars. The GTK toplevel is resizable and exposes the window-manager title buttons for minimize, maximize/restore and close.

## Window management

GTK controls the shell's own toplevel through GTK4 window APIs. Tiling and cascading across unrelated application windows are delegated to the active Wayland/X11 compositor; a GTK client must not pretend it can override compositor policy. The menu reports that boundary rather than faking placement.

## Sound and feedback

When `canberra-gtk-play` is installed, the shell requests desktop-theme sounds for click, menu, open and Properties events. Sound playback is optional and failure to find the sound helper does not block desktop interaction.

## Filesystem boundary

The context menu's Rename action is session-local guidance, not a host file rename. Properties describes the selected application card, not actual inode metadata. Real file rename, deletion, copy, permissions and mount actions require a VFS-backed file manager and must use the user's credentials.

## Native Koronos boundary

This is a GTK4 application running in a Linux userspace image. It is not the Koronos compositor, a bare-metal GUI, or proof of native Koronos userspace readiness. The native Koronos path still needs graphics/input device services, process launch, VFS file operations, focus/input routing and compositor integration. The native-init exit-78 gate remains authoritative.
