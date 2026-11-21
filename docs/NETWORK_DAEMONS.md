# Network daemons and service providers

This integration stages the Linux reference providers into the OS image; it does not claim that the Koronos-native service manager or daemon ABI is complete. The native Koronos port remains a separate implementation and runtime-acceptance task.

## Daemons and protocols

| Capability | Provider | Package | Service unit |
|---|---|---|---|
| SSH and SFTP | OpenSSH server | `openssh-server` | `ssh.service` |
| HTTP | nginx | `nginx` | `nginx.service` |
| HTTP / httpd | Apache HTTP Server | `apache2` | `apache2.service` |
| FTP / FTPS-capable server | vsftpd | `vsftpd` | `vsftpd.service` |
| TFTP | tftpd-hpa | `tftpd-hpa` | `tftpd-hpa.service` |

SFTP is the SSH file-transfer subsystem, not FTP and not a separate clear-text daemon. The build stages server packages and records package outcomes; it does not enable listeners at image-build time by policy.

## Security defaults

- SSH: use key authentication, disable root login and password authentication where operationally possible, restrict users/groups, and expose only on administrator-selected interfaces.
- HTTP: run worker processes unprivileged, keep document roots read-only where possible, and configure TLS at deployment.
- FTP: keep disabled by default; if enabled, require explicit administrator configuration and prefer FTPS or SFTP. Never use anonymous write access.
- TFTP: keep disabled by default; use a dedicated read-only directory and restrict it to a trusted provisioning network. TFTP has no authentication or encryption.
- Firewall policy, service-account permissions, logs, update policy and port exposure must be reviewed before activation.

## Build and verification

The package provider installer is part of the image build. Its JSON report distinguishes installed, unavailable and failed packages. A package being installed is not proof that the daemon starts, is correctly confined, or works under Koronos. Verify the executable and ELF header for the target architecture, service unit resolution, configuration syntax, socket binding policy, and QEMU runtime startup before marking a service as runtime-ready.

Linux reference packages are provider dependencies, not proprietary Windows/macOS OS binaries. Do not copy host OS binaries across incompatible ABIs.
