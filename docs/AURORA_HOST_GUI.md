# Aurora Host GUI and Cross-Platform Runtime

## Linux
Use the Docker GUI with read-only host /proc and /sys mounts and optional /dev access. The host scanner uses PCI/USB/DMI interfaces.

## Windows
Run the same Aurora web GUI in Docker Desktop and launch hardware/host-agents/windows/scan-hardware.ps1 on the Windows host. Docker Desktop can use Linux or Windows containers; the container must not be assumed to expose the complete Windows PnP namespace.

## macOS
Run the GUI container through Docker Desktop and launch hardware/host-agents/macos/scan-hardware.sh on the macOS host. DriverKit/System Extensions remain native macOS constructs and are integrated through compatibility metadata rather than copied into the Linux container.

Docker Desktop documents different host backends and VM boundaries on Linux/Windows, so the architecture separates GUI from the privileged native hardware agent.
