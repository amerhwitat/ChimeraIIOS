# Native desktop session launcher: measured evidence boundary

`tools/runtime/chimera-native-session.py` is a real launcher/supervisor for the
four named desktop sessions (`aurora`, `marine`, `freexp`, `freewin11`). It
starts a display server and the session shell from binaries found in a real
rootfs/build tree and records only measured facts:

- shell and display-server paths, executable bit, ELF magic and SHA-256;
- display socket existence before and after launch;
- `/dev/input/event*` device nodes (or an explicitly synthetic harness directory);
- display-server and shell PIDs, `/proc/<pid>/exe`, and exit status from `wait()`;
- stability after a bounded monitoring window.

It never emits a hardcoded PASS. `session_ready` is set only when every observed
check holds and no synthetic harness is used. `production_acceptance` and
`conformance_claim` are always false. A `--harness` run is explicitly labelled
`synthetic_harness=true` and can produce `checks_satisfied` but never
`session_ready` or `koronos_native_boot_verified`.

## Measured local result (WSL Ubuntu, 2026-11-24)

All four sessions were run with `--preflight-only`. Every run returned exit 78
(`blocked`) and wrote `build/native-sessions/<session>/preflight.json` with
`session_ready=false`. The exact missing pieces measured in this environment:

1. No `chimera-desktop-shell` ELF in any candidate rootfs path; the build-tree
   path `build/desktop/bin/chimera-desktop-shell` is also absent. GTK4
   development headers are not installed, so the GTK shell cannot be compiled
   here (`pkg-config gtk4` reports `Package gtk4 was not found`).
2. No Wayland compositor ELF (`labwc`, `weston` or `sway`) in the rootfs or on
   `PATH`; no X11 server (`Xvfb`/`Xorg`) either. `xinit`, `xinput`, `xprop` and
   `xwininfo` are also absent.
3. No input device nodes under `/dev/input` (the directory does not exist).
   `/dev/dri/card0` exists but that alone is not a graphics session.

A WSLg Wayland socket was observed at `/run/user/1000/wayland-0`, but a socket
plus a host kernel is **not** proof of a Koronos native graphics/compositor/input
stack. It is recorded as a measurement only.

## What was genuinely implemented

The launcher's process supervision, binary validation, socket/device probing,
health monitoring and evidence JSON generation are implemented. The synthetic
harness test uses two compiled ELF stubs and a synthetic input directory to
prove those mechanics end-to-end while explicitly refusing to claim readiness.

## What remains missing for item 7

- An ISO/rootfs that actually stages `chimera-desktop-shell` and a compositor
  (`labwc`) with its configuration and clients.
- A bootable Koronos environment with DRM/evdev/graphics and input providers;
  this WSL host cannot boot Koronos.
- Real observed compositor process, shell process, input attachment and stable
  health for all four sessions. None of these were observed here.
- Application-launch smoke tests inside the running native sessions.

No release is certified or published by this work.
