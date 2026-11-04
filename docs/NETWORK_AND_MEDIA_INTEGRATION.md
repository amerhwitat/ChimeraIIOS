# Chimera II OS network browsing, directory services and optical media

## Components

- **SMB client/server:** Samba `smbclient`, `smbd`, and `cifs-utils` provide SMB2/SMB3 browsing, file sharing and CIFS mounts.
- **Windows network discovery:** `wsdd` implements WS-Discovery used by modern Windows Network discovery. Avahi advertises and discovers `_smb._tcp` services using DNS-SD. Legacy NetBIOS/SMB1 browsing is intentionally not enabled.
- **Active Directory:** `realmd` + `adcli` perform administrator-authorized domain joining; SSSD provides identity lookup and PAM/NSS integration. Kerberos uses `krb5-user`.
- **LDAP:** `ldap-utils` provides `ldapsearch`; use `ldaps://` with a trusted CA. The CLI wrapper defaults to LDAPS.
- **Optical media:** `chimera-media-mount.sh` mounts ISO-9660/UDF images and optical devices read-only with `nodev,nosuid,noexec`.
- **Filesystem hierarchy:** `chimera-init-layout.sh` creates standard Linux FHS directories plus Chimera-specific namespaces. It does not mount `/proc`, `/sys`, or `/dev`.

## Install and enable

The ISO runtime package layer includes the package set in `iso/manifests/network-filesystem-packages.txt`. On Ubuntu/Debian hosts:

    sudo apt-get update
    sudo apt-get install samba smbclient cifs-utils winbind libnss-winbind libpam-winbind \
      krb5-user realmd adcli sssd sssd-ad sssd-ldap sssd-tools ldap-utils \
      libsasl2-modules-gssapi-mit avahi-daemon avahi-utils wsdd gvfs-backends \
      udisks2 util-linux xorriso udftools

Install the tools into `/usr/local/sbin` and service/config assets into their corresponding `/etc` or `/usr/lib/systemd/system` locations. Enable only services needed by the machine:

    sudo systemctl enable --now smbd.service
    sudo systemctl enable --now avahi-daemon.service
    sudo systemctl enable --now chimera-wsdd.service

For a server, create `/srv/smb/public`, create a dedicated `smbusers` group, review `services/network/smb.conf.example`, and add authorized users with `smbpasswd`. Do not expose writable guest shares by default.

## Network browsing

    chimera-network-browser.sh discover
    chimera-network-browser.sh shares fileserver.example.org
    chimera-network-browser.sh browse fileserver.example.org Documents
    sudo chimera-network-browser.sh mount-share fileserver.example.org Documents /mnt/chimera/network/documents alice
    sudo chimera-network-browser.sh unmount-share /mnt/chimera/network/documents

SMB mounts negotiate SMB 3.1.1 and use a temporary mode-0600 credentials file under /run. The file is deleted after the mount attempt; mounts use nodev,nosuid,noexec.

`smbclient` prompts for credentials when required. The wrapper explicitly restricts the client to SMB2/SMB3. WSD and DNS-SD discovery are link-local network mechanisms and normally do not cross routers/VLANs without a configured relay.

## Active Directory

First inspect the domain:

    chimera-network-browser.sh domain-discover example.org

Then, with authorization from the domain administrator:

    sudo chimera-network-browser.sh domain-join example.org --user administrator

The `realm` helper prompts for the password; the password is not placed in argv or shell history. Ensure DNS points to AD DNS, system time is synchronized, and Kerberos realm discovery succeeds. Domain join changes machine identity and must not run automatically during ISO build or first boot.

## LDAP

    chimera-network-browser.sh ldap-search ldaps://ldap.example.org \
      'dc=example,dc=org' '(objectClass=person)'

For authenticated searches, append a bind DN; ldapsearch prompts for the password. Install the issuing CA certificate into the system trust store. Plain `ldap://` is rejected unless `CHIMERA_LDAP_ALLOW_PLAINTEXT=1` is explicitly set for an isolated test environment.

## Mount optical media

    sudo chimera-media-mount.sh list
    sudo chimera-media-mount.sh mount-iso /path/to/image.iso
    sudo chimera-media-mount.sh mount-optical /dev/sr0
    sudo chimera-media-mount.sh unmount /mnt/chimera/media/image.iso

Mountpoints are restricted to `/mnt/chimera/media`. Media is read-only, non-executable and cannot provide device nodes or setuid files. For file-manager integration, expose mount state through UDisks2/GVfs; do not run arbitrary media autorun content.

## Filesystem hierarchy

    sudo chimera-init-layout.sh --root /mnt/target-root

The script creates directories only. The installer remains responsible for mounting the target root, EFI System Partition, swap, `/proc`, `/sys`, `/dev`, and `/run` in the correct boot/install sequence.

## Security and operational notes

- SMB1, NT1, guest access and NetBIOS ports are disabled in the supplied server example.
- Prefer SMB3 encryption/signing on untrusted networks; firewall TCP/445 to trusted LANs.
- AD domain joining is an explicit administrator operation; no credentials are embedded in the image.
- LDAP certificate validation is mandatory by default.
- Keep SMB TCP/445 and WSD UDP/3702 plus TCP/5357 restricted to trusted local networks; WSD multicast is link-local by default. Do not enable `smbd`, WS-Discovery, or Avahi on public/untrusted interfaces without firewall policy.
- These components integrate established Linux services; they do not reimplement SMB, Kerberos, LDAP or AD wire protocols from scratch.
