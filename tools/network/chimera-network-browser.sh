#!/usr/bin/env bash
set -Eeuo pipefail
usage() {
cat <<'EOF'
Chimera II OS network browser and directory integration
Usage:
  chimera-network-browser.sh discover
  chimera-network-browser.sh shares HOST
  chimera-network-browser.sh browse HOST [SHARE]
  chimera-network-browser.sh domain-discover DOMAIN
  chimera-network-browser.sh domain-join DOMAIN [--user USER]
  chimera-network-browser.sh ldap-search URI BASE_DN FILTER [BIND_DN]
Security: SMB2/3 only; no SMB1/guest fallback. Passwords are prompted interactively.
EOF
}
need(){ command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Missing command: $1" >&2; exit 127; }; }
die(){ echo "[ERROR] $*" >&2; exit 2; }
valid_host(){ [[ "$1" =~ ^[A-Za-z0-9._:-]+$ ]] || die "Invalid host name/address."; }
discover(){
  echo "== DNS-SD SMB services =="
  command -v avahi-browse >/dev/null 2>&1 && avahi-browse --resolve --terminate _smb._tcp 2>/dev/null || true
  echo "== Windows WS-Discovery =="
  if command -v wsdd >/dev/null 2>&1; then echo "wsdd installed; check systemctl status chimera-wsdd.service"; else echo "Install wsdd to enable Windows network discovery."; fi
  echo "Use 'shares HOST' to enumerate a server with interactive authentication."
}
shares(){ valid_host "$1"; need smbclient; smbclient -L "//$1" --option='client min protocol=SMB2' --option='client max protocol=SMB3'; }
browse(){
  local host="$1" share="\${2:-}" target
  valid_host "$host"
  [[ -z "$share" || "$share" =~ ^[A-Za-z0-9._$ -]+$ ]] || die "Invalid share name."
  target="//$host"; [[ -z "$share" ]] || target="$target/$share"
  need smbclient
  smbclient "$target" --option='client min protocol=SMB2' --option='client max protocol=SMB3'
}
domain_discover(){ [[ "$1" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid DNS domain."; need realm; realm discover --verbose "$1"; }
domain_join(){
  (( EUID == 0 )) || die "Domain join requires root."
  local domain="$1" user="" arg; shift
  while (($#)); do arg="$1"; shift; case "$arg" in --user) (($#)) || die "--user requires a value"; user="$1"; shift;; *) die "Unknown option: $arg";; esac; done
  [[ "$domain" =~ ^[A-Za-z0-9.-]+$ ]] || die "Invalid DNS domain."
  [[ -n "$user" ]] || read -r -p "Domain join account: " user
  [[ "$user" =~ ^[A-Za-z0-9._@-]+$ ]] || die "Invalid account."
  need realm; need adcli; need sssd
  echo "[INFO] realm will securely prompt for credentials; no password is passed in argv."
  realm join --membership-software=adcli --client-software=sssd --user="$user" "$domain"
  realm list "$domain"
}
ldap_search(){
  local uri="$1" base="$2" filter="$3" bind_dn="\${4:-}"
  [[ "$uri" == ldaps://* ]] || { [[ "$uri" == ldap://* && "\${CHIMERA_LDAP_ALLOW_PLAINTEXT:-0}" == 1 ]] || die "Use ldaps://; plaintext LDAP is disabled by default."; }
  need ldapsearch
  local -a args=(-LLL -o nettimeout=10 -H "$uri" -b "$base" "$filter")
  [[ -z "$bind_dn" ]] || args=(-LLL -o nettimeout=10 -H "$uri" -D "$bind_dn" -W -b "$base" "$filter")
  LDAPTLS_REQCERT=demand ldapsearch "\${args[@]}"
}
main(){
  (($#)) || { usage; return 0; }; local cmd="$1"; shift
  case "$cmd" in
    -h|--help|help) usage;;
    discover) (($#==0)) || die "discover takes no args"; discover;;
    shares) (($#==1)) || die "shares HOST"; shares "$1";;
    browse) (($#>=1 && $#<=2)) || die "browse HOST [SHARE]"; browse "$@";;
    domain-discover) (($#==1)) || die "domain-discover DOMAIN"; domain_discover "$1";;
    domain-join) (($#>=1)) || die "domain-join DOMAIN [--user USER]"; domain_join "$@";;
    ldap-search) (($#>=3 && $#<=4)) || die "ldap-search URI BASE_DN FILTER [BIND_DN]"; ldap_search "$@";;
    *) die "Unknown command: $cmd (use --help)";;
  esac
}
main "$@"
