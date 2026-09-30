#!/bin/sh
set -eu
mkdir -p /var/crash/chimera /var/log/mesgs
printf '%s [CRASH] Chimera II OS entered failure handler\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /var/log/mesgs
DUMP=$(/usr/bin/chimera-crash-dump.sh 2>/dev/null || true)
clear 2>/dev/null || true
printf '\033[1;37;41m CHIMERA II OS — SYSTEM FAILURE \033[0m\n\n'
printf 'A fatal system condition was detected.\nCrash dump: %s\n\n' "$DUMP"
printf 'F1 Dump memory   F2 Logs   F3 Processes   R Reboot   S Shutdown\n\nRecent /var/log/mesgs:\n'
tail -n 30 /var/log/mesgs 2>/dev/null || true
