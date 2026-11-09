#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOTFS="${1:?usage: build-chimera-native-tools.sh ROOTFS}"
[[ -d "$ROOTFS" && -x "$ROOTFS/bin/sh" ]] || { echo "invalid target rootfs" >&2; exit 2; }
CXX="${CXX:-g++}"
command -v "$CXX" >/dev/null 2>&1 || { echo "C++ compiler required: $CXX" >&2; exit 2; }
OUT="$ROOTFS/usr/bin"
install -d "$OUT" "$ROOTFS/usr/share/chimera/commands" "$ROOTFS/usr/share/chimera/help/tools/help" "$ROOTFS/usr/share/chimera/help/web"
manifest="$ROOTFS/usr/share/chimera/commands/hosted-tools.tsv"
: > "$manifest"

rootfs_has_executable() {
  local name="$1" dir
  for dir in /usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin; do
    [[ -x "$ROOTFS$dir/$name" ]] && return 0
  done
  return 1
}

"$CXX" -std=c++20 -O2 -Wall -Wextra -Werror "$ROOT/userland/commands/chmctl.cpp" -o "$ROOTFS/usr/bin/chmctl"
printf 'chmctl|/usr/bin/chmctl|compiled-linux-userspace\n' >> "$manifest"

# Compile the durable Hive registry CLI from its real storage engine.
"$CXX" -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
  -I"$ROOT/userspace/hive" \
  "$ROOT/userspace/hive/registryctl.cpp" \
  "$ROOT/userspace/hive/registry_store.cpp" \
  -o "$OUT/chimera-registry"
ln -sfn chimera-registry "$OUT/hivectl"
printf 'chimera-registry|/usr/bin/chimera-registry|compiled-hive-registry-store\n' >> "$manifest"
printf 'hivectl|/usr/bin/hivectl|verified-alias-to-chimera-registry\n' >> "$manifest"

ln -sfn chmctl "$OUT/chimeractl"
printf 'chimeractl|/usr/bin/chimeractl|verified-alias-to-chmctl\n' >> "$manifest"

# Genuine diagnostics and package/update frontends; no placeholder commands.
install -D -m 0755 "$ROOT/tools/commands/chimera-info.py" "$OUT/chimera-info"
printf 'chimera-info|/usr/bin/chimera-info|python3-system-information\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/commands/chimera-doctor.py" "$OUT/chimera-doctor"
printf 'chimera-doctor|/usr/bin/chimera-doctor|python3-nondestructive-diagnostics\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/commands/chimera-update.sh" "$OUT/chimera-update"
printf 'chimera-update|/usr/bin/chimera-update|apt-update-and-explicit-upgrade\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/chimera-package-manager.sh" "$OUT/chimera-pkg"
ln -sfn chimera-pkg "$OUT/chimera-package"
printf 'chimera-package|/usr/bin/chimera-package|verified-alias-to-chimera-pkg\n' >> "$manifest"

# Install Kore's actual user-space control client and its service frontend.
install -D -m 0755 "$ROOT/tools/runtime/chimera-korectl.py" "$OUT/korectl"
install -D -m 0755 "$ROOT/tools/runtime/chimera-service.py" "$OUT/chimera-service"
printf 'korectl|/usr/bin/korectl|python3-kore-request-client\n' >> "$manifest"
printf 'chimera-service|/usr/bin/chimera-service|korectl-service-frontend\n' >> "$manifest"

# Build the real Chimera assembler, disassembler and rewriter from repository source.
cmake -S "$ROOT/tools/chimera-asm" -B "$ROOT/build/chimera-asm-host" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build "$ROOT/build/chimera-asm-host" --parallel "$(nproc)"
DESTDIR="$ROOTFS" cmake --install "$ROOT/build/chimera-asm-host"
ln -sfn chimera-as "$OUT/chimera-asm"
ln -sfn chimera-dis "$OUT/chimera-disasm"
printf 'chimera-asm|/usr/bin/chimera-asm|cmake-built-cxx20-assembler\n' >> "$manifest"
printf 'chimera-disasm|/usr/bin/chimera-disasm|cmake-built-cxx20-disassembler\n' >> "$manifest"

install -D -m 0755 "$ROOT/tools/help/chimera-help" "$ROOTFS/usr/share/chimera/help/tools/help/chimera-help"
cp -a "$ROOT/tools/help/." "$ROOTFS/usr/share/chimera/help/tools/help/"
[[ -s "$ROOT/web/man_pages.json" ]] && install -D -m 0644 "$ROOT/web/man_pages.json" "$ROOTFS/usr/share/chimera/help/web/man_pages.json"
cat > "$OUT/chimera-help" <<'HELP'
#!/bin/sh
export CHIMERA_HELP_ROOT=/usr/share/chimera/help
exec python3 /usr/share/chimera/help/tools/help/chimera-help "$@"
HELP
chmod 0755 "$OUT/chimera-help"
printf 'chimera-help|/usr/bin/chimera-help|python3-help-database\n' >> "$manifest"

install -D -m 0755 "$ROOT/tools/display/chimera-display" "$OUT/chimera-display"
printf 'chimera-display|/usr/bin/chimera-display|wlr-randr-or-xrandr\n' >> "$manifest"
install -D -m 0755 "$ROOT/sdk/bin/chimera-python" "$OUT/chimera-python"
printf 'chimera-python|/usr/bin/chimera-python|python3-wrapper\n' >> "$manifest"
if rootfs_has_executable java; then
  install -D -m 0755 "$ROOT/sdk/bin/chimera-java" "$OUT/chimera-java"
  printf 'chimera-java|/usr/bin/chimera-java|java-wrapper\n' >> "$manifest"
fi
install -D -m 0755 "$ROOT/tools/branding/chimera-background" "$OUT/chimera-background"
printf 'chimera-background|/usr/bin/chimera-background|file-backed-background-manager\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/display/chimera-gpu-driver-manager" "$OUT/chimera-gpu-driver-manager"
printf 'chimera-gpu-driver-manager|/usr/bin/chimera-gpu-driver-manager|apt-pciutils-driver-manager\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/drivers/chimera-hardware-drivers" "$OUT/chimera-hardware-drivers"
printf 'chimera-hardware-drivers|/usr/bin/chimera-hardware-drivers|udev-kmod-firmware-manager\n' >> "$manifest"
install -D -m 0755 "$ROOT/tools/drivers/chimera-driver-panel.py" "$OUT/chimera-driver-panel"
printf 'chimera-driver-panel|/usr/bin/chimera-driver-panel|tk-hardware-panel\n' >> "$manifest"

install -D -m 0644 "$ROOT/system/shell/chimera-shell.sh" "$ROOTFS/usr/share/chimera/shell/chimera-shell.sh"
cat > "$OUT/chimera-shell" <<'SHELL'
#!/bin/sh
export CHIMERA_COMMAND_CATALOG=/usr/share/chimera/commands/chimera-command-list.json
exec bash --rcfile /etc/profile.d/chimera-shell.sh -i "$@"
SHELL
chmod 0755 "$OUT/chimera-shell"
install -D -m 0644 "$ROOT/system/shell/chimera-shell.sh" "$ROOTFS/etc/profile.d/chimera-shell.sh"
printf 'chimera-shell|/usr/bin/chimera-shell|bash-profile-integration\n' >> "$manifest"

if rootfs_has_executable terminald; then
  install -D -m 0755 "$ROOT/tools/terminal/chimera-terminal" "$OUT/chimera-terminal"
  printf 'chimera-terminal|/usr/bin/chimera-terminal|terminald-client\n' >> "$manifest"
fi
install -D -m 0644 "$ROOT/system/commands/chimera-command-list.json" "$ROOTFS/usr/share/chimera/commands/chimera-command-list.json"
if [[ -s "$ROOT/system/commands/chimera-arabic.json" ]]; then
  install -D -m 0644 "$ROOT/system/commands/chimera-arabic.json" "$ROOTFS/usr/share/chimera/commands/chimera-arabic.json"
fi
if [[ -s "$ROOT/config/drivers/hardware-driver-policy.json" ]]; then
  install -D -m 0644 "$ROOT/config/drivers/hardware-driver-policy.json" "$ROOTFS/usr/share/chimera/drivers/hardware-driver-policy.json"
fi
if [[ -s "$ROOT/config/drivers/audio-driver-manifest.json" ]]; then
  install -D -m 0644 "$ROOT/config/drivers/audio-driver-manifest.json" "$ROOTFS/usr/share/chimera/drivers/audio-driver-manifest.json"
fi
sha256sum "$manifest" > "$ROOTFS/usr/share/chimera/commands/hosted-tools.SHA256SUMS"
echo "Compiled and staged genuine hosted-Linux Chimera tools; Koronos-native execution remains a separate ABI target."
