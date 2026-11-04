# SMB, Microsoft network browsing and directory services

Chimera integrates maintained protocol implementations rather than claiming a newly written SMB or Kerberos stack.

## SMB client and browser
DNS-SD discovery queries Avahi for _smb._tcp advertisements. Share enumeration delegates SMB2/SMB3 negotiation and authentication to Samba's smbclient. Kerberos mode uses the existing credential cache. SMB1 and anonymous access are disabled by default. Install Samba client and Avahi packages to enable discovery. The helper returns hosts and shares as JSON; a file-manager integration must render these results.

## Optional SMB server
The opt-in smbd unit runs the distribution's Samba daemon. The default configuration exports no shares, disables NetBIOS and SMB1, requires server signing and denies guest mapping. Administrators must configure shares, ACLs, firewall rules and accounts before enabling it. This is not a new SMB protocol implementation.

## Active Directory and LDAP
The domain helper uses realmd/adcli for discovery and interactive join, with SSSD/Kerberos as identity/authentication providers. LDAP password operations require TLS and signing. DNS SRV records and synchronized time are preconditions. Credentials are entered interactively and never stored in source control or registry hives. Directory browsing should use ldapsearch with StartTLS or LDAPS, never a clear-text password over plain LDAP.

## Optical media
chimera-iso-mount accepts an ISO image or optical block device and tries ISO9660 then UDF, always read-only with nosuid,nodev,noexec. It requires root and refuses non-empty or already-mounted targets.

## Linux filesystem hierarchy
The target follows FHS conventions: /usr/bin, /usr/sbin, /usr/lib, /usr/share, /etc, /var, /run, /dev, /proc, /sys, /home, /root, /opt, /srv, /mnt, /media and /tmp. Chimera payloads live under /system/chimera; machine policy under /etc/chimera; mutable state under /var/lib/chimera; volatile state under /run/chimera. /bin, /sbin, /lib and /lib64 are compatibility symlinks into /usr where supported.
