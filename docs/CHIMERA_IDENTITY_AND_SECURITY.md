# Chimera II OS Identity, Active Directory, and Filesystem Security

Chimera uses Unix-compatible local identity files and administrator-controlled directory integration.

## Local accounts
- /etc/passwd
- /etc/shadow
- /etc/group
- /etc/gshadow

UID/GID 0 is root. Root password initialization is interactive and updates only the root records. Passwords are hashed with crypt(3) using a kernel random source and are never accepted as command-line arguments.

Commands include chm-user-setup, chm-passwd, chm-groupadd, chm-usermod, chm-groupmod, chm-perms, and chm-security-selftest.

## Active Directory
chm-ad configure creates staged Kerberos, NSS, and PAM provider configuration for SSSD or Samba/winbind. chm-ad join requires an explicit interactive administrator confirmation and delegates credential entry to realm or Samba. No password is stored by Chimera.

The design uses DNS, Kerberos, LDAP, SMB, and synchronized time, while local files remain first in NSS.

## Filesystem security
The policy includes Unix mode bits, ownership, POSIX/NFSv4-compatible ACL adapters, setuid/setgid/sticky bits, mount controls, capabilities, and MAC-provider hooks. Shadow, gshadow, Kerberos keytabs, and SSSD configuration are protected resources.

All privileged identity mutations require UID 0. Account database writes use file locks and atomic replacement. Remote root login remains disabled by policy.
