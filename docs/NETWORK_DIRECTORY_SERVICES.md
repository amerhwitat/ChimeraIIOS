# SMB networking, Windows network browsing and directory services

## Architecture

Chimera uses maintained protocol implementations rather than a new, unreviewed SMB/LDAP wire stack.

- **SMB client and share browsing:** Samba smbclient enumerates shares on an explicit server. The browser uses Kerberos (-k) and SMB2 or newer; it never falls back to guest or plaintext passwords.
- **Windows host discovery:** the Network app sends a bounded WS-Discovery Probe to the local-link multicast group and queries DNS-SD _smb._tcp through Avahi. It does not scan address ranges. A discovered endpoint is only a candidate; the user explicitly selects a host before SMB share enumeration.
- **SMB server:** upstream Samba smbd provides SMB2/SMB3 serving. It is disabled by default, has no exported shares, and ships bound to loopback until an administrator configures interfaces, shares, ACLs and firewall rules. wsdd is an optional host-announcement daemon, not the discovery client.
- **Active Directory:** realmd + adcli + SSSD + MIT Kerberos perform explicit domain enrollment and identity lookup. Obtain a Kerberos ticket first (kinit user@REALM). The GUI validates a private, user-owned FILE credential cache, then invokes realm join --no-password through pkexec/PolicyKit for an explicit administrator authentication prompt. It never collects or stores a domain password.
- **LDAP:** ldapsearch uses GSSAPI/Kerberos and mandatory TLS validation. ldap:// is accepted only with StartTLS (-ZZ); ldaps:// uses certificate validation. Anonymous binds and simple plaintext binds are not used by the helper.
- **Authorization:** domain join and server enablement require administrator policy. Never store passwords in registry hives or command-line arguments.

## Tools

services/network/smb-browse.py --network performs local-link WS-Discovery and DNS-SD discovery.
services/network/smb-browse.py files.example.org lists disk shares from an explicit SMB2/3 host using the existing Kerberos ticket cache.
services/network/directoryctl.py status reports joined realms.
services/network/directoryctl.py join example.org --user administrator requests a domain join using an existing Kerberos ticket.
services/network/directoryctl.py ldap-search ldaps://dc.example.org dc=example,dc=org '(objectClass=computer)' performs a bounded GSSAPI LDAP query.

Package installation is declared in system/integrations/*.json and staged by live-image/build.sh.

## Service boundary

Samba, SSSD, Kerberos, realmd and OpenLDAP client tools are Linux live-edition user-space integrations. They are not Koronos kernel features. A native Koronos SMB client/server, RPC stack, TLS stack, LDAP client and AD/Kerberos implementation are not claimed.
