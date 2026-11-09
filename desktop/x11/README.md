# X.Org / X11 provider

This directory defines the optional X11 provider stack for Aurora Glass and Marine Blue.

The ISO provider installer installs upstream Ubuntu packages for X.Org, xinit, Xauthority, Xwayland, Xvfb, X11 utilities and Openbox. The desktop shell can then be launched as an X11 client in a Linux-compatible runtime.

## Runtime status

**Provider packages declared; Koronos bare-metal X11 runtime is not yet verified.**

Installing Xorg does not itself provide the kernel interfaces it needs. A production session still requires working Linux syscall coverage, DRM/KMS, VT switching, input devices and session management. The desktop must not silently fall back to Xorg when those interfaces are unavailable.

## Manual launcher

Run `bash desktop/x11/start-session.sh aurora` or `bash desktop/x11/start-session.sh marine or `bash desktop/x11/start-session.sh freexp`` only after the X11 runtime has been validated. The launcher intentionally refuses by default until the explicit opt-in variable is set:

`CHIMERA_X11_FORCE_UNVERIFIED=1`

This override is for controlled development testing, not a production-ready status.
