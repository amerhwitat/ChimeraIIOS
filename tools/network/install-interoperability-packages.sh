#!/usr/bin/env bash
set -euo pipefail
packages=(samba smbclient cifs-utils avahi-daemon realmd adcli sssd sssd-tools krb5-user ldap-utils python3-tk gvfs-backends)
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y "${packages[@]}"
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y samba samba-client cifs-utils avahi realmd adcli sssd krb5-workstation openldap-clients python3-tkinter gvfs-smb
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Sy --needed samba smbclient cifs-utils avahi realmd adcli sssd krb5 openldap tk gvfs
else
  echo "Unsupported package manager; install Samba, Avahi, realmd, adcli, SSSD, Kerberos and OpenLDAP client packages manually." >&2
  exit 2
fi
