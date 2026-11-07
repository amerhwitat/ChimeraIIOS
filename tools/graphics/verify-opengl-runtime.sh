#!/usr/bin/env bash
set -euo pipefail
# Validate the hosted Linux OpenGL/EGL/GLES userspace installed in Chimera/Octavian.
# This checks library availability and, when available, a real display context.
for soname in libGL.so.1 libEGL.so.1 libGLESv2.so.2 libgbm.so.1; do
  if ! ldconfig -p 2>/dev/null | grep -Fq "$soname"; then
    printf 'MISSING graphics library: %s\n' "$soname" >&2
    exit 1
  fi
done
printf '%s\n' 'OpenGL userspace libraries: present'
if printenv DISPLAY >/dev/null 2>&1 && command -v glxinfo >/dev/null 2>&1; then
  glxinfo -B
elif command -v eglinfo >/dev/null 2>&1; then
  eglinfo -B
else
  printf '%s\n' 'No active X11/EGL diagnostic context; library presence only (not a rendered-frame test).'
fi
if [[ -d /dev/dri ]]; then
  printf 'DRM devices: '
  find /dev/dri -maxdepth 1 -type c -printf '%f ' 2>/dev/null || true
  printf '\n'
else
  printf '%s\n' 'No /dev/dri nodes: hardware acceleration is unavailable in this runtime; software rendering may still be possible.'
fi
