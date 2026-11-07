#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: test-aurora-terminal-shell-centers.sh ROOTFS}"
shell_list="$(chroot "$ROOTFS" /usr/local/bin/aurora-shell-center --list)"
grep -q '^bash|bash$' <<<"$shell_list"
shell_output="$(chroot "$ROOTFS" /usr/local/bin/aurora-shell-center bash -c 'printf CHIMERA_SHELL_CENTER_OK')"
[[ "$shell_output" == "CHIMERA_SHELL_CENTER_OK" ]]
test -x "$ROOTFS/usr/local/bin/aurora-terminal-center"
test -s "$ROOTFS/usr/share/chimera/aurora/terminal-shell-installed.tsv"
test -s "$ROOTFS/usr/share/chimera/aurora/shells-installed.tsv"
terminal_entries="$(find "$ROOTFS/usr/share/applications" -maxdepth 1 -type f -name 'chimera-terminal-*.desktop' | wc -l)"
((terminal_entries >= 10)) || { echo "Expected multiple installed terminal launchers, got $terminal_entries" >&2; exit 1; }
test -s "$ROOTFS/usr/share/applications/chimera-shell-center.desktop"
echo "PASS: Aurora Shell Center launches a verified shell and terminal desktop entries are staged."
