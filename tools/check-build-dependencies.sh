#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
AUTO_INSTALL="${CHIMERA_AUTO_INSTALL_DEPS:-1}"
APT_RETRY="${CHIMERA_APT_RETRIES:-3}"
export DEBIAN_FRONTEND=noninteractive

say(){ printf '\n[%s] %s\n' "$1" "$2"; }
die(){ echo "[ERROR] $*" >&2; exit 2; }

declare -a REQUIRED_COMMANDS=(
  bash python3 cmake gcc g++ ld as make pkg-config git curl wget file rsync
  cpio gzip xz tar busybox awk sed grep sha256sum numfmt stat find sort
  xorriso grub-mkrescue grub-file mcopy mformat grub-mkimage
  unsquashfs mksquashfs rsvg-convert nasm
)

declare -A COMMAND_PACKAGE=(
  [bash]=bash [python3]=python3 [cmake]=cmake [gcc]=gcc [g++]=g++
  [ld]=binutils [as]=binutils [make]=make [pkg-config]=pkg-config
  [git]=git [curl]=curl [wget]=wget [file]=file [rsync]=rsync
  [cpio]=cpio [gzip]=gzip [xz]=xz-utils [tar]=tar [busybox]=busybox
  [awk]=gawk [sed]=sed [grep]=grep [sha256sum]=coreutils [numfmt]=coreutils
  [stat]=coreutils [find]=findutils [sort]=coreutils
  [xorriso]=xorriso [grub-mkrescue]=grub-common [grub-file]=grub-common
  [mcopy]=mtools [mformat]=mtools [grub-mkimage]=grub-common
  [unsquashfs]=squashfs-tools [mksquashfs]=squashfs-tools
  [rsvg-convert]=librsvg2-bin [nasm]=nasm
)

# Additional packages used by the build scripts and generated applications.
declare -a BUILD_PACKAGES=(
  build-essential binutils gcc g++ make cmake ninja-build pkg-config
  python3 python3-dev python3-venv python3-pip python3-setuptools python3-wheel
  git curl wget ca-certificates file rsync cpio gzip xz-utils bzip2 tar busybox
  xorriso grub-common grub2-common grub-pc-bin grub-efi-amd64-bin mtools
  squashfs-tools librsvg2-bin nasm
  openssl libssl-dev zlib1g-dev libffi-dev libreadline-dev libsqlite3-dev
  libncurses-dev libboost-dev gawk sed grep coreutils findutils util-linux
)

declare -a OPTIONAL_PACKAGES=(
  clang llvm lld gdb lldb yasm valgrind strace
  nodejs npm ruby perl php lua5.4 golang-go rustc cargo
  openjdk-21-jdk default-jdk openjdk-17-jdk qemu-system-x86
  dotnet-sdk-10.0 dotnet-sdk-9.0 dotnet-sdk-8.0
  gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
  gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
)

missing=()
for c in "${REQUIRED_COMMANDS[@]}"; do
  command -v "$c" >/dev/null 2>&1 || missing+=("$c")
done

if (( ${#missing[@]} == 0 )); then
  say DEPS "All mandatory ISO build commands are installed."
else
  say DEPS "Missing mandatory commands: ${missing[*]}"
fi

if (( ${#missing[@]} > 0 )) && [[ "$AUTO_INSTALL" == "1" ]]; then
  if ! command -v apt-get >/dev/null 2>&1 || [[ ! -f /etc/debian_version ]]; then
    die "Automatic installation currently supports Debian/Ubuntu hosts. Missing: ${missing[*]}"
  fi

  apt_prefix=()
  if [[ "$(id -u)" -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || die "sudo is required for automatic dependency installation."
    apt_prefix=(sudo)
  fi

  say DEPS "Refreshing APT indexes and installing the complete build dependency set."
  for attempt in $(seq 1 "$APT_RETRY"); do
    if "${apt_prefix[@]}" apt-get update; then break; fi
    [[ "$attempt" -lt "$APT_RETRY" ]] || die "apt-get update failed after $APT_RETRY attempts."
    sleep 2
  done
  "${apt_prefix[@]}" apt-get install -y --no-install-recommends "${BUILD_PACKAGES[@]}"

  missing=()
  for c in "${REQUIRED_COMMANDS[@]}"; do
    command -v "$c" >/dev/null 2>&1 || missing+=("$c")
  done
fi

(( ${#missing[@]} == 0 )) || die "Mandatory dependencies remain missing: ${missing[*]}"

install_optional_toolchains() {
  [[ "${CHIMERA_INSTALL_OPTIONAL_DEPS:-0}" == "1" ]] || return 0

  say DEPS "Installing optional application toolchains and compatibility runtimes."
  if ! command -v apt-get >/dev/null 2>&1 || [[ ! -f /etc/debian_version ]]; then
    say DEPS "Non-Debian host detected; optional toolchain auto-install is skipped."
    return 0
  fi

  local apt_prefix=()
  [[ "$(id -u)" -eq 0 ]] || apt_prefix=(sudo)
  "${apt_prefix[@]}" apt-get update -qq || {
    echo "[WARN] Optional toolchain APT refresh failed; continuing." >&2
    return 0
  }

  apt_install_candidates() {
    local command_name="$1"; shift
    command -v "$command_name" >/dev/null 2>&1 && return 0
    local candidates=("$@") available=() p
    for p in "${candidates[@]}"; do
      apt-cache show "$p" >/dev/null 2>&1 && available+=("$p")
    done
    if (( ${#available[@]} == 0 )); then
      echo "[WARN] No APT package candidate available for $command_name: ${candidates[*]}" >&2
      return 0
    fi
    echo "[DEPS] Installing $command_name from: ${available[*]}"
    "${apt_prefix[@]}" apt-get install -y --no-install-recommends "${available[@]}" ||
      echo "[WARN] Could not install optional $command_name; continuing." >&2
  }

  apt_install_candidates javac openjdk-21-jdk default-jdk openjdk-17-jdk
  apt_install_candidates java openjdk-21-jdk default-jdk openjdk-17-jdk
  apt_install_candidates rustc rustc
  apt_install_candidates cargo cargo
  apt_install_candidates node nodejs
  apt_install_candidates npm npm
  apt_install_candidates dotnet dotnet-sdk-10.0 dotnet-sdk-9.0 dotnet-sdk-8.0

  local optional_missing=() c
  for c in javac java rustc cargo node npm dotnet; do
    command -v "$c" >/dev/null 2>&1 || optional_missing+=("$c")
  done
  if (( ${#optional_missing[@]} > 0 )); then
    echo "[INFO] Optional toolchains still unavailable after installation: ${optional_missing[*]}"
    echo "[INFO] The ISO build remains allowed to continue; affected applications will be marked unavailable."
  else
    say DEPS "All optional application toolchains are installed and discoverable."
  fi
}
say DEPS "Mandatory dependency verification passed."
if [[ "${CHIMERA_INSTALL_OPTIONAL_DEPS:-0}" == "1" ]]; then
  if command -v apt-get >/dev/null 2>&1 && [[ -f /etc/debian_version ]]; then
    apt_prefix=()
    [[ "$(id -u)" -eq 0 ]] || apt_prefix=(sudo)
    optional_available=()
    for p in "${OPTIONAL_PACKAGES[@]}"; do
      if apt-cache show "$p" >/dev/null 2>&1; then
        optional_available+=("$p")
      else
        echo "[INFO] Optional package unavailable in configured repositories: $p"
      fi
    done
    if (( ${#optional_available[@]} > 0 )); then
      # Avoid one large optional transaction: Ubuntu HWE and non-HWE QEMU
      # providers can conflict. Install optional packages independently.
      for p in "${optional_available[@]}"; do
        case "$p" in
          qemu-user-static|qemu-user-binfmt|qemu-user-binfmt-hwe)
            echo "[INFO] Skipping conflicting QEMU user-mode provider: $p"
            continue ;;
        esac
        if "${apt_prefix[@]}" apt-get install -y --no-install-recommends "$p"; then
          echo "[DEPS] installed optional: $p"
        else
          echo "[WARN] Optional package failed and was skipped: $p" >&2
        fi
      done
    fi
  fi
fi

install_optional_toolchains

# Validate the repository scripts that are part of the ISO pipeline.
declare -a PIPELINE_SCRIPTS=(
  tools/build-network-toolkit.sh tools/build-toolchain-bundle.sh
  tools/fetch-driver-payloads.sh tools/build-koronos-targets.sh
  tools/fetch-foreign-runtimes.sh tools/build-compatibility-binaries.sh
  tools/build-mobile-edition.sh tools/build-desktop-binaries.sh
  tools/build-live-boot-binaries.sh boot/iso/build-iso.sh
)
for f in "${PIPELINE_SCRIPTS[@]}"; do
  [[ -f "$ROOT/$f" ]] || die "Required pipeline script is missing: $f"
  [[ -x "$ROOT/$f" ]] || chmod +x "$ROOT/$f"
done

# Verify the Python tooling used by the build without downloading arbitrary packages.
python3 - <<'PY'
import importlib.util
mods = ["json", "pathlib", "subprocess", "hashlib"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Missing Python stdlib modules: " + ", ".join(missing))
print("[DEPS] Python build runtime verified.")
PY

say DEPS "Dependency preflight complete."
