#!/usr/bin/env bash
set -euo pipefail
usage(){ cat <<'EOF'
Usage: install-opengl-opencv.sh --install | --verify
Installs or verifies Mesa/OpenGL, GLFW and OpenCV development/runtime packages.
EOF
}
mode="${1:-}"
case "$mode" in
 --install)
  case "$(uname -s)" in
   Linux)
    if command -v apt-get >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y libgl1-mesa-dev libegl1-mesa-dev libglfw3-dev libopencv-dev mesa-utils xvfb pkg-config
    elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y mesa-libGL-devel mesa-libEGL-devel glfw-devel opencv-devel mesa-demos xorg-x11-server-Xvfb pkgconf-pkg-config
    elif command -v pacman >/dev/null 2>&1; then sudo pacman -Sy --needed --noconfirm mesa glfw opencv mesa-utils xorg-server-xvfb pkgconf
    else echo "Unsupported Linux package manager." >&2; exit 69; fi ;;
   Darwin) command -v brew >/dev/null || { echo "Install Homebrew first." >&2; exit 69; }; brew install mesa glfw opencv pkg-config ;;
   *) echo "Use the Linux development environment (or WSL) for the Chimera graphics SDK." >&2; exit 69 ;;
  esac ;;
 --verify)
  command -v pkg-config >/dev/null || { echo "pkg-config missing" >&2; exit 1; }
  pkg-config --modversion gl
  pkg-config --modversion glfw3
  pkg-config --modversion opencv4
  if command -v opencv_version >/dev/null 2>&1; then opencv_version; fi
  if command -v glxinfo >/dev/null 2>&1; then
   if [[ -n "${DISPLAY:-}" ]]; then glxinfo -B
   elif command -v xvfb-run >/dev/null 2>&1; then LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a glxinfo -B
   else echo "GL libraries found; no display/Xvfb available for renderer probe." >&2; fi
  fi ;;
 -h|--help) usage ;;
 *) usage >&2; exit 64 ;;
esac
