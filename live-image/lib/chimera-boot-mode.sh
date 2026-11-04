#!/usr/bin/env bash
set -euo pipefail
cmdline="$(cat /proc/cmdline 2>/dev/null || true)"
boot_mode="live"
for token in $cmdline; do
  case "$token" in
    chimera.mode=*) boot_mode="${token#chimera.mode=}" ;;
  esac
done
case "$boot_mode" in
  live) exec /usr/bin/python3 /usr/local/bin/aurora-kiosk.py ;;
  installer)
    echo "[Installer] Starting the configured graphical installer."
    if command -v calamares >/dev/null 2>&1 && [[ -f /etc/calamares/settings.conf ]]; then
      exec sudo -E calamares --debug
    fi
    echo
    echo "INSTALLER NOT CONFIGURED"
    echo "No OS-specific Calamares configuration is installed. No disk changes were made."
    echo "Production installation requires partition, EFI, bootloader, target-root"
    echo "and post-install validation modules for this operating system."
    exec xterm -fullscreen -e /bin/bash -lc 'echo "Installer unavailable: OS-specific settings/modules are missing."; echo "No disk changes were made."; exec bash -l'
    ;;
  recovery) exec xterm -fullscreen -e /usr/local/sbin/chimera-recovery ;;
  *)
    echo "[Boot] Unknown chimera.mode=$boot_mode; refusing implicit action." >&2
    exec xterm -fullscreen -e /bin/bash -lc 'echo "Unknown boot mode. No disk changes were made."; exec bash -l'
    ;;
esac
