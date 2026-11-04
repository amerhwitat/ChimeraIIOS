#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Chimera II OS network browser and directory integration
Usage:
  chimera-network-browser.sh discover
  chimera-network-browser.sh shares HOST
  chimera-network-browser.sh browse HOST [SHARE]
  sudo chimera-network-browser.sh mount-share HOST SHARE MOUNTPOINT [USER]
  sudo chimera-network-browser.sh unmount-share MOUNTPOINT
  chimera-network-browser.sh domain-discover DOMAIN
  sudo chimera-network-browser.sh domain-join DOMAIN [--user USER]
  chimera-network-browser.sh ldap-search URI BASE_DN FILTER [BIND_DN]

Security: SMB2/3 only. Passwords are prompted interactively and never placed in argv.
EOF
}
need() { command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Missing command: $1" >&2; exit 127; }; }
die() { echo "[ERROR] $*" >&2; exit 2; }
valid_host() { [[ "$1" =~ ^[A-Za-z0-9._:-]+$ ]] || die "Invalid host name/address."; }
valid_share() {
  local share="${1:-}" base="${1:-}" dollar
  [[ -z "$share" ]] && return 0
  printf -v dollar '%b' '\044'
  # Permit Windows hidden shares ending in a literal dollar without embedding it in a regex.
  [[ "$base" == *"$dollar" ]] && base="${base%?}"
  [[ -n "$base" && "$base" != *[!A-Za-z0-9._\ -]* ]] || die "Invalid share name."
}

discover() {
  echo "== DNS-SD SMB services =="
  if command -v avahi-browse >/dev/null 2>&1; then
    avahi-browse --resolve --terminate _smb._tcp 2>/dev/null || true
  fi
  echo "== Windows WS-Discovery =="
  if command -v wsdd >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1; then
    echo "Probing local link for WSD devices (10 seconds)..."
    local rc=0
    timeout 10s wsdd --discovery --no-host --shortlog -v || rc=$?
    [[ "$rc" == 0 || "$rc" == 124 ]] || echo "[WARN] WSD probe exited with status $rc" >&2
  else
    echo "Install wsdd to enable Windows network discovery."
  fi
  echo "Use 'shares HOST' to enumerate a server with interactive authentication."
}

shares() {
  valid_host "$1"
  need smbclient
  smbclient -L "//$1" --option='client min protocol=SMB2' --option='client max protocol=SMB3'
}

browse() {
  local host="$1" share="${2:-}" target
  valid_host "$host"
  valid_share "$share"
  target="//$host"
  [[ -z "$share" ]] || target="$target/$share"
  need smbclient
  smbclient "$target" --option='client min protocol=SMB2' --option='client max protocol=SMB3'
}

mount_share() {
  (( EUID == 0 )) || die "SMB mounting requires root; use sudo."
  local host="$1" share="$2" target="$3" user="${4:-}" cred password rc
  valid_host "$host"
  valid_share "$share"
  target="$(realpath -m -- "$target")"
  [[ "$target" == /mnt/chimera/network/* ]] || die "Mountpoint must resolve below /mnt/chimera/network."
  need mount.cifs
  if [[ -z "$user" ]]; then read -r -p "SMB username: " user; fi
  [[ -n "$user" && "$user" != *'='* ]] || die "Invalid SMB username."
  read -r -s -p "SMB password: " password
  printf '\n'
  install -d -m 0755 /run/chimera
  cred="$(mktemp /run/chimera/smb-credentials.XXXXXX)"
  chmod 0600 "$cred"
  printf 'username=%s\npassword=%s\n' "$user" "$password" > "$cred"
  unset password
  install -d -m 0755 "$target"
  mountpoint -q "$target" && die "Already mounted: $target"
  if mount -t cifs "//$host/$share" "$target" -o "credentials=$cred,vers=3.1.1,sec=ntlmssp,iocharset=utf8,nosuid,nodev,noexec,file_mode=0640,dir_mode=0750"; then
    rm -f -- "$cred"
    echo "[SUCCESS] Mounted //$host/$share at $target using SMB 3.1.1."
  else
    rc=$?
    rm -f -- "$cred"
    return "$rc"
  fi
}

unmount_share() {
  (( EUID == 0 )) || die "SMB unmount requires root."
  local target
  target="$(realpath -m -- "$1")"
  [[ "$target" == /mnt/chimera/network/* ]] || die "Mountpoint must resolve below /mnt/chimera/network."
  mountpoint -q "$target" || die "Not mounted: $target"
  umount -- "$target"
}

domain_discover() {
  [[ "$1" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid DNS domain."
  need realm
  realm discover --verbose "$1"
}

domain_join() {
  (( EUID == 0 )) || die "Domain join requires root."
  local domain="$1" user="" arg
  shift
  while (($#)); do
    arg="$1"; shift
    case "$arg" in
      --user) (($#)) || die "--user requires a value"; user="$1"; shift ;;
      *) die "Unknown option: $arg" ;;
    esac
  done
  [[ "$domain" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid DNS domain."
  [[ -n "$user" ]] || read -r -p "Domain join account: " user
  [[ "$user" =~ ^[A-Za-z0-9._@-]+$ ]] || die "Invalid account."
  need realm
  need adcli
  need sssd
  echo "[INFO] realm prompts securely; no password is passed in argv."
  realm join --membership-software=adcli --client-software=sssd --user="$user" "$domain"
  realm list "$domain"
}

ldap_search() {
  local uri="$1" base="$2" filter="$3" bind_dn="${4:-}"
  [[ "$uri" == ldaps://* ]] || {
    [[ "$uri" == ldap://* && "${CHIMERA_LDAP_ALLOW_PLAINTEXT:-0}" == 1 ]] ||
      die "Use ldaps://; plaintext LDAP is disabled by default."
  }
  need ldapsearch
  local -a args=(-LLL -o nettimeout=10 -H "$uri" -b "$base" "$filter")
  [[ -z "$bind_dn" ]] || args=(-LLL -o nettimeout=10 -H "$uri" -D "$bind_dn" -W -b "$base" "$filter")
  LDAPTLS_REQCERT=demand ldapsearch "${args[@]}"
}

main() {
  (($#)) || { usage; return 0; }
  local cmd="$1"; shift
  case "$cmd" in
    -h|--help|help) usage ;;
    discover) (($# == 0)) || die "discover takes no args"; discover ;;
    shares) (($# == 1)) || die "shares HOST"; shares "$1" ;;
    browse) (($# >= 1 && $# <= 2)) || die "browse HOST [SHARE]"; browse "$@" ;;
    mount-share) (($# >= 3 && $# <= 4)) || die "mount-share HOST SHARE MOUNTPOINT [USER]"; mount_share "$@" ;;
    unmount-share) (($# == 1)) || die "unmount-share MOUNTPOINT"; unmount_share "$1" ;;
    domain-discover) (($# == 1)) || die "domain-discover DOMAIN"; domain_discover "$1" ;;
    domain-join) (($# >= 1)) || die "domain-join DOMAIN [--user USER]"; domain_join "$@" ;;
    ldap-search) (($# >= 3 && $# <= 4)) || die "ldap-search URI BASE_DN FILTER [BIND_DN]"; ldap_search "$@" ;;
    *) die "Unknown command: $cmd (use --help)" ;;
  esac
}
main "$@"
