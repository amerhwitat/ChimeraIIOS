#!/usr/bin/env bash
set -Eeuo pipefail
usage() { cat <<'EOF'
Chimera II OS package manager bridge
Usage: chimera-pkg status | databases | list [manager] | search <query> [manager] | install <package> [manager] | remove <package> [manager] | update [manager]
Managers: auto, apt, dnf, pacman, zypper, apk, snap, flatpak, brew/homebrew, nix, npm, yarn, pnpm, corepack.
Only installed providers are called. Auto mode may retry read-only searches with another available provider; install/remove/update never silently switch providers.
EOF
}
die() { printf '[chimera-pkg] ERROR: %s\n' "$*" >&2; exit 2; }
have() { command -v "$1" >/dev/null 2>&1; }
detect_manager() {
  local requested="${1:-auto}"
  case "$requested" in
    auto|"")
      for m in apt dnf pacman zypper apk snap flatpak brew nix npm yarn pnpm corepack; do
        case "$m" in
          apt) have apt-get && { printf apt; return; } ;;
          dnf|pacman|zypper|apk|snap|flatpak|brew|nix|npm|yarn|pnpm|corepack) have "$m" && { printf '%s' "$m"; return; } ;;
        esac
      done
      printf none ;;
    homebrew) have brew && printf brew || printf missing ;;
    apt) have apt-get && printf apt || printf missing ;;
    dnf|pacman|zypper|apk|snap|flatpak|brew|nix|npm|yarn|pnpm|corepack) have "$requested" && printf '%s' "$requested" || printf missing ;;
    *) die "unknown package manager: $requested" ;;
  esac
}
manager_status() {
  local m exe state
  for m in apt dnf pacman zypper apk snap flatpak brew nix npm yarn pnpm corepack; do
    exe="$m"; [[ "$m" != apt ]] || exe=apt-get
    if have "$exe"; then state=available; else state=not-installed; fi
    printf '%-10s %s\n' "$m" "$state"
  done
}
action="${1:-}"
[[ -n "$action" ]] || { usage; exit 2; }
if [[ "$action" == "-h" || "$action" == "--help" ]]; then usage; exit 0; fi
if [[ "$action" == status ]]; then manager_status; exit 0; fi
if [[ "$action" == databases ]]; then
  catalog="${CHIMERA_DATABASE_CATALOG:-/usr/share/chimera/database/databases.json}"
  [[ -r "$catalog" ]] || catalog="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/registry/databases.json"
  python3 - "$catalog" <<'PYDB'
import json,sys
with open(sys.argv[1],encoding="utf-8") as f: data=json.load(f)
for engine in data.get("engines",[]):
    print("{:<16} {:<22} {:<24} {}".format(engine["id"],engine.get("kind","unknown"),engine.get("license","unspecified"),engine.get("role","")))
PYDB
  exit 0
fi
manager="${CHIMERA_PKG_MANAGER:-auto}"
if [[ $# -gt 0 ]]; then
  last="${!#}"
  case "$last" in apt|dnf|pacman|zypper|apk|snap|flatpak|brew|homebrew|nix|npm|yarn|pnpm|corepack|auto) manager="$last"; set -- "${@:1:$#-1}" ;; esac
fi
requested_manager="$manager"
manager="$(detect_manager "$manager")"
[[ "$manager" != missing && "$manager" != none ]] || die "requested package manager is not installed"
validate_package() { [[ -n "$1" && "$1" != -* && "$1" != *$'\n'* && "$1" != *$'\r'* ]] || die "invalid package name"; }
run_privileged() {
  if (( EUID == 0 )); then "$@"
  elif have sudo; then sudo -- "$@"
  else die "this action needs root; run as root or install sudo"; fi
}
run_readonly() {
  local rc=0 candidate
  "$@" && return 0
  rc=$?
  [[ "$requested_manager" == auto ]] || return "$rc"
  # Retry only read-only searches; never replay a mutating command on another provider.
  for candidate in apt dnf pacman zypper apk flatpak brew nix npm yarn pnpm; do
    [[ "$candidate" != "$manager" ]] || continue
    [[ "$(detect_manager "$candidate")" != missing ]] || continue
    printf '[chimera-pkg] Primary search provider %s failed; trying %s.\n' "$manager" "$candidate" >&2
    case "$candidate" in
      apt) apt-cache search -- "$query" ;;
      dnf) dnf search "$query" ;;
      pacman) pacman -Ss "$query" ;;
      zypper) zypper search "$query" ;;
      apk) apk search "$query" ;;
      flatpak) flatpak search "$query" ;;
      brew) brew search "$query" ;;
      nix) nix search nixpkgs "$query" ;;
      npm) npm search "$query" ;;
      yarn) yarn npm search "$query" ;;
      pnpm) pnpm search "$query" ;;
    esac && return 0
  done
  return "$rc"
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
      npm) npm ls -g --depth=0 ;;
      yarn) yarn global list ;;
      pnpm) pnpm ls -g --depth=0 ;;
      corepack) corepack --version; corepack pnpm --version 2>/dev/null || true; corepack yarn --version 2>/dev/null || true ;;
    esac ;;
  search)
    [[ $# -ge 1 ]] || die "search requires a query"
    query="$1"
    case "$manager" in
      apt) run_readonly apt-cache search -- "$query" ;;
      dnf) run_readonly dnf search "$query" ;;
      pacman) run_readonly pacman -Ss "$query" ;;
      zypper) run_readonly zypper search "$query" ;;
      apk) run_readonly apk search "$query" ;;
      snap) snap find "$query" ;;
      flatpak) run_readonly flatpak search "$query" ;;
      brew) run_readonly brew search "$query" ;;
      nix) run_readonly nix search nixpkgs "$query" ;;
      npm) run_readonly npm search "$query" ;;
      yarn) run_readonly yarn npm search "$query" ;;
      pnpm) run_readonly pnpm search "$query" ;;
      corepack) corepack pnpm search "$query" ;;
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
      npm:install) npm install --global -- "$pkg" ;;
      npm:remove) npm uninstall --global -- "$pkg" ;;
      yarn:install) yarn global add "$pkg" ;;
      yarn:remove) yarn global remove "$pkg" ;;
      pnpm:install) pnpm add --global "$pkg" ;;
      pnpm:remove) pnpm remove --global "$pkg" ;;
      corepack:install) corepack install --global "$pkg" ;;
      *) die "install/remove is not supported for provider $manager" ;;
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
      npm) npm update --global ;;
      yarn) yarn global upgrade ;;
      pnpm) pnpm update --global ;;
      corepack) corepack up ;;
    esac ;;
  *) usage >&2; die "unsupported action: $action" ;;
esac
