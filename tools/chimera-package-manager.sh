#!/usr/bin/env bash
set -Eeuo pipefail
usage() { cat <<'EOF'
Chimera II OS package manager bridge
Usage: chimera-pkg status | list [manager] | search <query> [manager] | install <package> [manager] | remove <package> [manager] | update [manager]
Managers: auto, apt, dnf, pacman, zypper, apk, snap, flatpak, brew/homebrew, nix.
CHIMERA_PKG_MANAGER may select a default manager. Only installed providers are called.
EOF
}
die() { printf '[chimera-pkg] ERROR: %s\n' "$*" >&2; exit 2; }
have() { command -v "$1" >/dev/null 2>&1; }
detect_manager() {
  local requested="${1:-auto}"
  case "$requested" in
    auto|"") for m in apt dnf pacman zypper apk snap flatpak brew nix; do
      case "$m" in
        apt) have apt-get && { printf apt; return; } ;;
        dnf) have dnf && { printf dnf; return; } ;;
        pacman) have pacman && { printf pacman; return; } ;;
        zypper) have zypper && { printf zypper; return; } ;;
        apk) have apk && { printf apk; return; } ;;
        snap) have snap && { printf snap; return; } ;;
        flatpak) have flatpak && { printf flatpak; return; } ;;
        brew) have brew && { printf brew; return; } ;;
        nix) have nix && { printf nix; return; } ;;
      esac
    done; printf none ;;
    homebrew) have brew && printf brew || printf missing ;;
    apt) have apt-get && printf apt || printf missing ;;
    dnf|pacman|zypper|apk|snap|flatpak|brew|nix) have "$requested" && printf '%s' "$requested" || printf missing ;;
    *) die "unknown package manager: $requested" ;;
  esac
}
manager_status() {
  local m exe state
  for m in apt dnf pacman zypper apk snap flatpak brew nix; do
    case "$m" in apt) exe=apt-get;; *) exe="$m";; esac
    if have "$exe"; then state=available; else state=not-installed; fi
    printf '%-10s %s\n' "$m" "$state"
  done
}
action="${1:-}"
[[ -n "$action" ]] || { usage; exit 2; }
if [[ "$action" == "-h" || "$action" == "--help" ]]; then usage; exit 0; fi
if [[ "$action" == status ]]; then manager_status; exit 0; fi
manager="${CHIMERA_PKG_MANAGER:-auto}"
if [[ $# -gt 0 ]]; then
  last="${!#}"
  case "$last" in apt|dnf|pacman|zypper|apk|snap|flatpak|brew|homebrew|nix|auto) manager="$last"; set -- "${@:1:$#-1}" ;; esac
fi
manager="$(detect_manager "$manager")"
[[ "$manager" != missing && "$manager" != none ]] || die "requested package manager is not installed"
validate_package() { [[ -n "$1" && "$1" != -* && "$1" != *$'\n'* && "$1" != *$'\r'* ]] || die "invalid package name"; }
run_privileged() {
  if (( EUID == 0 )); then "$@"
  elif have sudo; then sudo -- "$@"
  else die "this action needs root; run as root or install sudo"; fi
}
case "$action" in
  list)
    case "$manager" in
      apt) dpkg-query -W -f='${binary:Package}\t${Version}\n' ;;
      dnf) dnf list --installed ;;
      pacman) pacman -Q ;;
      zypper) zypper search --installed-only ;;
      apk) apk info -v ;;
      snap) snap list ;;
      flatpak) flatpak list --app ;;
      brew) brew list --versions ;;
      nix) nix profile list ;;
    esac ;;
  search)
    [[ $# -ge 1 ]] || die "search requires a query"; query="$1"
    case "$manager" in
      apt) apt-cache search -- "$query" ;;
      dnf) dnf search "$query" ;;
      pacman) pacman -Ss "$query" ;;
      zypper) zypper search "$query" ;;
      apk) apk search "$query" ;;
      snap) snap find "$query" ;;
      flatpak) flatpak search "$query" ;;
      brew) brew search "$query" ;;
      nix) nix search nixpkgs "$query" ;;
    esac ;;
  install|remove)
    [[ $# -ge 1 ]] || die "$action requires a package"; pkg="$1"; validate_package "$pkg"
    case "$manager:$action" in
      apt:install) run_privileged apt-get install -- "$pkg" ;;
      apt:remove) run_privileged apt-get remove -- "$pkg" ;;
      dnf:install) run_privileged dnf install -y "$pkg" ;;
      dnf:remove) run_privileged dnf remove -y "$pkg" ;;
      pacman:install) run_privileged pacman -S --needed "$pkg" ;;
      pacman:remove) run_privileged pacman -R "$pkg" ;;
      zypper:install) run_privileged zypper --non-interactive install "$pkg" ;;
      zypper:remove) run_privileged zypper --non-interactive remove "$pkg" ;;
      apk:install) run_privileged apk add "$pkg" ;;
      apk:remove) run_privileged apk del "$pkg" ;;
      snap:install) run_privileged snap install "$pkg" ;;
      snap:remove) run_privileged snap remove "$pkg" ;;
      flatpak:install) flatpak install --user --assumeyes flathub "$pkg" ;;
      flatpak:remove) flatpak uninstall --user --assumeyes "$pkg" ;;
      brew:install) brew install "$pkg" ;;
      brew:remove) brew uninstall "$pkg" ;;
      nix:install) nix profile install "nixpkgs#$pkg" ;;
      nix:remove) nix profile remove "$pkg" ;;
    esac ;;
  update)
    case "$manager" in
      apt) run_privileged apt-get update && run_privileged apt-get upgrade ;;
      dnf) run_privileged dnf upgrade -y ;;
      pacman) run_privileged pacman -Syu ;;
      zypper) run_privileged zypper --non-interactive refresh && run_privileged zypper --non-interactive update ;;
      apk) run_privileged apk update && run_privileged apk upgrade ;;
      snap) run_privileged snap refresh ;;
      flatpak) flatpak update --user --assumeyes ;;
      brew) brew update && brew upgrade ;;
      nix) nix profile upgrade '.*' ;;
    esac ;;
  *) usage >&2; die "unsupported action: $action" ;;
esac
