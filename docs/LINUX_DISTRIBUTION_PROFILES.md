# Chimera II OS — Linux Distribution Profiles

Chimera II uses explicit distribution profiles rather than mixing package repositories.

Profiles cover Debian/Ubuntu/Mint/Kali, RHEL/Fedora/CentOS and compatible derivatives, SUSE/openSUSE, Arch/Manjaro, Gentoo, Alpine, Void, NixOS, Mageia, FreeBSD/OpenBSD/NetBSD, Solaris-family Unix, and native Chimera.

## Package-manager mapping

- Debian/Ubuntu/Mint/Kali: APT
- RHEL/Fedora/CentOS derivatives: DNF
- SUSE/openSUSE: Zypper
- Arch/Manjaro: pacman
- Gentoo: emerge
- Alpine: apk
- Void: xbps
- NixOS: nix
- BSD: pkg/pkg_add/pkgin

Arch's Rosetta documentation directly compares pacman, DNF, APT, Zypper and emerge. citeturn0search1 Ubuntu and Debian document APT as their package-management interface. citeturn0search0turn0search10 Red Hat documents DNF and its module/profile model. citeturn0search8 SUSE uses Zypper/libzypp. citeturn0search13 Kali uses Debian's APT stack. citeturn0search2turn0search4

## Profile management

The profile-management interface is designed around:

- `chm-profile list`
- `chm-profile show <name>`
- `chm-profile current`
- `chm-profile detect`
- `chm-profile use <name>`
- `chm-profile create <name>`
- `chm-profile clone <name>`
- `chm-profile export <name>`
- `chm-profile import <file>`
- `chm-profile reset`

Switching a profile changes command/package-manager mappings. It does not automatically rewrite repositories or install another distribution.

This separation is particularly important for Kali: Kali explicitly warns against adding Kali repositories to another distribution or mixing other distribution repositories into Kali because it can break installations. citeturn0search9

