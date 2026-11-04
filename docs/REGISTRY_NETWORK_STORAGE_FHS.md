# Registry, Microsoft network interoperability and storage layout

## Registry settings and Aurora editor

CHMRG01 stores versioned typed settings in separate machine, environment and kernel hives. The Aurora Registry Editor is a loopback-only web UI at 127.0.0.1:8765 backed by registryd over a Unix socket. Its API requires a per-user runtime capability token; the API process runs as the desktop user and does not elevate itself into the administrator group. The daemon checks Unix peer credentials and chimera-admin group membership. Writes are generation-checked, journaled and atomically persisted. Hardware identity, discovered CPU features, privilege policy, memory limits, SMP acknowledgements and other boot-critical values remain immutable through the editor. Never put passwords, Kerberos tickets, hashes or private keys in registry values.

## SMB and Microsoft network browsing

Use maintained Samba smbclient/smbd rather than a new SMB protocol stack. SMB2/3 only, mandatory signing, guest access disabled and NetBIOS/SMB1 disabled. Local-link browsing combines DNS-SD _smb._tcp and WS-Discovery; listing a server's shares is an explicit-target operation authenticated through the Kerberos credential cache. Server mode is opt-in and has no default shares or exposed interfaces. Modern Windows discovery is not the obsolete SMB1 browse-master protocol.

## Active Directory and LDAP

directory-discovery.py performs bounded DNS SRV lookups for LDAP/Kerberos domain controllers. directoryctl.py uses realmd + adcli + SSSD for administrator-authorized domain join. The GUI requires kinit first, validates the user's private FILE credential cache, and requests explicit PolicyKit authentication through pkexec; no password is passed on a command line. LDAP uses ldapsearch with GSSAPI and certificate validation. A join changes machine identity and system authentication configuration; it is never automatic. Credentials remain in Kerberos/keyring facilities, not registry files or command-line password arguments.

## ISO/CD/DVD

mount-image.py validates ISO-9660/UDF images and requests read-only loop mounts through udisks2. Physical optical drives are limited to /dev/srN and mounted read-only. Polkit decides which desktop user may mount media. Native Koronos VFS drivers and block-device integration are still required before this is a native-kernel mount implementation.

## Linux directory hierarchy

fhs-layout.json describes a merged-/usr FHS-compatible root. create-fhs-tree.py --root <staging-root> creates the directory skeleton inside an explicit image root and adds /bin, /sbin and /lib links only when absent. It never writes to the host root by default. /proc, /sys, /dev, /run and /tmp are mount points; the script does not mount them.
