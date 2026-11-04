# SMB, Microsoft network browsing and directory services

The Linux live edition integrates mature protocol implementations through
policy-checked Aurora IPC. These are user-space interoperability adapters, not
Koronos-native protocol stacks.

## Registry editor

Aurora's Registry Editor uses a local Unix-domain socket bridge to registryd.
The daemon checks SO_PEERCRED, permits reads from local users, restricts writes
to root or the chimera-admin group, checks a generation number on every write,
rejects protected CPU/identity/security/boot-critical keys, and commits a
versioned JSON source plus CHMRG01 binary hive through a write-ahead journal.
The GUI falls back to a read-only defaults view when the trusted native bridge
is unavailable. It does not directly write hive files.

## SMB client and Microsoft network browser

The Aurora Windows Network app uses Samba's smbclient for SMB2/SMB3 share
enumeration. Authentication uses the existing Kerberos credential cache;
anonymous and plaintext-password fallback are disabled. Local-link discovery
combines Avahi DNS-SD advertisements for _smb._tcp with a bounded WS-Discovery
multicast Probe. It does not scan arbitrary address ranges.

## Optional SMB server

The server uses the maintained Samba smbd implementation. It is disabled by
default, binds to loopback in the shipped configuration, exports no shares,
disables SMB1/NetBIOS and guest mapping, and requires server signing. An
administrator must explicitly configure interfaces, shares, ACLs and firewall
policy before exposing a network share. This is not a new SMB server stack.

## Active Directory and LDAP

Domain membership uses realmd/adcli/SSSD and requires an existing Kerberos
ticket. The GUI validates the user's private FILE cache and invokes the join
through pkexec/PolicyKit for explicit administrator authentication. The join
command does not accept a password argument. Directory
queries use OpenLDAP ldapsearch with GSSAPI; ldap:// requires StartTLS and
ldaps:// requires certificate validation. DNS SRV records and synchronized
time are preconditions. Passwords, tickets and keys are never stored in the
registry or source repository.

## Optical media

The Aurora Optical Media app validates ISO-9660 primary volume descriptors and
UDF recognition sequences before requesting a read-only udisks2 loop mount.
Physical CD/DVD mounting accepts only /dev/srN devices and requires blkid to
identify ISO9660 or UDF. Unmount removes loop devices after a successful
unmount. Mounting uses the Linux live kernel and udisks2, not Koronos VFS.

## Linux filesystem hierarchy

The installed tree follows FHS conventions: /usr/bin, /usr/sbin, /usr/lib,
/usr/share, /etc, /var, /run, /dev, /proc, /sys, /home, /root, /opt, /srv,
/mnt, /media and /tmp. Chimera payloads live under /system/chimera; machine
policy under /etc/chimera; mutable state under /var/lib/chimera; volatile
state under /run/chimera. usr-merged compatibility links /bin, /sbin, /lib
are created only when absent. The rootfs helper accepts an explicit staging root and refuses paths at or
under host system directories; use a dedicated staging directory under /tmp
or on a separate build volume.
