#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "$(id -u)" -ne 0 ]]; then echo "must run as root (inside the target rootfs chroot)" >&2; exit 2; fi
command -v apt-get >/dev/null && command -v apt-cache >/dev/null || { echo "APT is required for this provider installer" >&2; exit 2; }
declare -a candidates=(
  # POSIX and Linux command providers
  hicolor-icon-theme coreutils findutils grep sed gawk mawk diffutils patch util-linux procps psmisc
  bash
  busybox-static file less nano vim-tiny tree bc bsdextrautils debianutils
  iproute2 iputils-ping net-tools dnsutils curl wget openssh-client rsync
  lsof strace screen tmux whois traceroute mtr-tiny jq sqlite3 git
  e2fsprogs dosfstools parted gdisk kmod pciutils usbutils
  gzip bzip2 xz-utils zstd tar cpio unzip zip ncurses-bin
  # Open-source shells from the Aurora shell registry
  zsh fish dash mksh yash elvish nushell
  # Open-source terminal emulators from the Aurora terminal registry
  xterm gnome-terminal konsole xfce4-terminal foot kitty alacritty wezterm ghostty contour-terminal
  # Optional Windows command and PowerShell compatibility runtimes
  wine64 powershell
  # Mesa OpenGL/EGL/GLES userspace and diagnostic tools
  libgl1 libglx-mesa0 libegl1 libgles2 libgbm1 libgl1-mesa-dri mesa-utils libgl-dev libegl-dev libgles-dev
  # Multi-architecture user/system emulation providers for the ISA catalogue
  qemu-user-static qemu-system-x86 qemu-system-arm qemu-system-mips
  qemu-system-ppc qemu-system-misc simh
)
declare -a available=() missing=()
for pkg in "${candidates[@]}"; do
  if apt-cache show "$pkg" >/dev/null 2>&1; then available+=("$pkg"); else missing+=("$pkg"); fi
done
if (("${#available[@]}")); then
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${available[@]}"
fi
# Expose every applet actually compiled into BusyBox without replacing any
# existing GNU/system command. This gives the hosted editions a real fallback
# provider path for commands that do not have a dedicated package binary.
BB="$(command -v busybox || true)"
APPLET_DIR=/usr/lib/chimera/busybox-bin
busybox_applets=()
if [[ -n "$BB" ]]; then
  mkdir -p "$APPLET_DIR" /etc/profile.d
  while IFS= read -r applet; do
    [[ -n "$applet" && "$applet" != "busybox" ]] || continue
    busybox_applets+=("$applet")
    command -v "$applet" >/dev/null 2>&1 && continue
    ln -sfn "$BB" "$APPLET_DIR/$applet"
  done < <("$BB" --list)
  printf 'export PATH=%s:$PATH\\n' "$APPLET_DIR" > /etc/profile.d/90-chimera-busybox-path.sh
fi
mkdir -p /usr/share/chimera/runtime
python3 - "${available[*]}" "${missing[*]}" "${busybox_applets[*]}" <<'PY'
import json,sys
from datetime import datetime,timezone
out={"schema":"CHM-RUNTIME-PACKAGES-1","generated_utc":datetime.now(timezone.utc).isoformat(),"package_provider":"Debian APT","available_candidates":sys.argv[1].split(),"unavailable_candidates":sys.argv[2].split(),"busybox_applets":sys.argv[3].split(),"note":"Package availability and BusyBox applet presence are provider evidence, not proof of every catalogue command or ISA instruction's runtime semantics; see command and ISA audit reports."}
with open("/usr/share/chimera/runtime/package-install-report.json","w") as f: json.dump(out,f,indent=2); f.write("\n")
PY
printf '[RUNTIME] Installed %s available packages; %s candidates unavailable\n' "${#available[@]}" "${#missing[@]}"
