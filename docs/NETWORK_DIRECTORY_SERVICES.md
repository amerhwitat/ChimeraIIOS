# SMB networking, Windows network browsing and directory services

## Architecture

Chimera uses maintained protocol implementations rather than a new, unreviewed SMB/LDAP wire stack.

- **SMB client and browsing:** Samba \`smbclient\` enumerates shares on an explicit server. Kerberos credentials (\`-k\`) are used; there is no automatic guest/password fallback.
- **SMB server:** upstream Samba \`smbd\` provides SMB2/SMB3 serving. It is opt-in, has no exported shares by default, and must be restricted to administrator-selected interfaces and share ACLs.
- **Windows network discovery:** WS-Discovery (\`wsdd\`) is the primary modern Windows discovery integration. Avahi/mDNS is supplementary. NetBIOS/SMB1 browsing is not enabled by default.
- **Active Directory:** \`realmd\` + \`adcli\` + \`SSSD\` + MIT Kerberos perform explicit domain enrollment and identity lookup. Domain join is a privileged interactive action.
- **LDAP:** \`ldapsearch\` uses GSSAPI/Kerberos and mandatory TLS validation. LDAP simple binds with plaintext passwords are not used by the helper.
- **Authorization:** Aegis/polkit and the system account policy control domain joins, server enablement and share configuration. Never store passwords in registry hives or command-line arguments.

## Tools

\`services/network/smb-browse.py HOST\` lists disk shares from a named SMB2/3 host using the existing Kerberos ticket cache. It does not scan networks.

\`services/network/directoryctl.py status\` reports joined realms.
\`services/network/directoryctl.py join example.org --user administrator\` requests an explicit domain join.
\`services/network/directoryctl.py ldap-search ldaps://dc.example.org dc=example,dc=org '(objectClass=computer)'\` performs a bounded GSSAPI LDAP query.

Package installation is declared in \`system/integrations/*.json\`; a package build must still resolve distro package versions and include the selected dependencies in the image.

## Service boundary

Samba, SSSD, Kerberos, realmd and OpenLDAP client tools are user-space integrations for the Linux live edition. They are not Koronos kernel features. A native Koronos SMB client/server, RPC stack, TLS stack, LDAP client and AD/Kerberos implementation are not claimed.
