# Chimera II OS Web Administration Console

The Chimera web console provides browser-based administration of a Chimera II OS host, inspired by the workflow of Cockpit while using Chimera's own service, security, container, and diagnostics interfaces.

## Access

The service binds to 127.0.0.1:8765 by default.

Create a token:

    sudo tools/web/init-chimera-web-token.sh
    sudo systemctl enable --now chimera-web

Then open http://127.0.0.1:8765/ and enter the token stored in /etc/chimera/web.token.

For remote administration, explicitly configure a trusted network bind and HTTPS certificate/key. Do not expose the HTTP listener directly to an untrusted network.

## Administration areas

- System overview, kernel, hostname, uptime and load
- systemd service inventory and controlled service actions
- local user inventory
- network interfaces, routes and NetworkManager status
- disks, filesystems and mounts
- journal logs
- diagnostic report
- Podman containers, images and pods
- controlled container lifecycle actions
- reboot and power-off
- audit logging

## Security model

The web API does not expose an arbitrary shell endpoint. Operations are allow-listed and authenticated with a bearer token. Privileged actions are still subject to the operating-system permissions of the web service.

The default policy is localhost-only. HTTPS can be enabled with CHIMERA_WEB_CERT and CHIMERA_WEB_KEY.

## Chimera integration

The service is installed under /usr/share/chimera/web/chimera_web.py, with its systemd unit at chimera-web.service and policy metadata under system/security/chimera_web_policy.json.

The console is intended to become the administration front end for Koronos, Kore, Aegis, Spotnik, Nucleus, Hive, Aurora and the container/virtualization subsystems as those native APIs mature.
