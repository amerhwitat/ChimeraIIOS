# Chimera II Hardware Scanner

Aurora Hardware Scanner normalizes host hardware for Koronos/Driver Manager.

Linux uses /proc, /sys, lspci, lsusb and dmidecode when available. Windows uses PowerShell PnP/CIM queries. macOS uses system_profiler/ioreg. A container cannot magically access the complete Windows/macOS host hardware namespace, so Windows/macOS use a native host-agent contract; Linux can use read-only /proc,/sys and optional /dev.
