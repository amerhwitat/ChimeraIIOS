#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root after installing Chimera II OS." >&2
  exit 1
fi

systemctl daemon-reload
systemctl enable --now chimera-kernel.service

cat <<'EOF'

Chimera kernel startup is enabled.

Aurora is exposed as a standard Wayland session:
  /usr/share/wayland-sessions/aurora.desktop

For automatic graphical login, configure the installed display manager's
normal autologin/session mechanism to select "Aurora (Chimera II)". This
keeps authentication, seat allocation, logind, GPU permissions, and the
Wayland session lifecycle under the platform display manager instead of
running a compositor as root.

Optional system-service launch (advanced/embedded deployments):
  systemctl enable --now aurora-session@<user>.service
EOF
