# Chimera II OS ISO runner (candidate)

This image boots the Chimera II OS ISO **inside QEMU**. It is a virtual-machine runner, not a native kernel-in-container implementation and not a claim that production userspace is ready.

Build from a CI-produced candidate ISO:

```sh
mkdir -p dist
cp output.iso dist/output.iso
docker build -f docker/iso-runner/Dockerfile -t ghcr.io/amerhwitat/chimera-ii-os-iso-runner:candidate .
```

Run the boot menu over VNC (port 5901):

```sh
docker run --rm -p 5901:5901 -e FIRMWARE=bios ghcr.io/amerhwitat/chimera-ii-os-iso-runner:candidate
docker run --rm -p 5901:5901 -e FIRMWARE=uefi ghcr.io/amerhwitat/chimera-ii-os-iso-runner:candidate
```

Set `QEMU_DISPLAY=none` for headless runs or adjust `MEMORY` and `CPUS`. VNC has no password in this development runner; expose port 5901 only to trusted hosts.

The ISO can show its boot menu and exercise kernel/target diagnostics, but Live-to-Aurora, completed installation/reboot, real recovery repair, and AP-backed SMP remain separate production acceptance gates. This tag is a development candidate, not a stable release.
