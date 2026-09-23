# Podman Containerization and Node Web Control

Chimera II integrates Podman as an OCI container engine through an explicit profile. Podman is daemonless, supports rootless operation, manages images, containers and pods, and provides Docker-CLI-compatible commands. citeturn0search3turn0search6

## Integration

The profile covers images, containers, pods, volumes, networks, build/pull/push, logs, exec, health checks, Quadlet, Kubernetes YAML and controlled auto-update.

Quadlet provides declarative container/pod/volume/network definitions integrated with systemd. citeturn0search0turn0search2

## Node web control

services/chimera-web/chimera_web.py provides a node-local web UI.

Defaults: 127.0.0.1:8765, Bearer token authentication, no unauthenticated startup, no arbitrary shell execution, allow-listed Podman read operations, allow-listed container lifecycle operations, and Chimera status/diagnostics.

The service deliberately does not expose the Podman socket directly. Podman supports Unix-socket and SSH remote connections; direct unauthenticated TCP is disabled in the Chimera profile. citeturn0search3

## Security

The web layer never escalates privileges. Container names are restricted to safe identifiers and actions are allow-listed. Remote exposure should use authenticated HTTPS/VPN or Podman's SSH transport.

Podman supports rootless containers and network isolation; host networking and privileged containers are not defaults in this integration. citeturn0search5turn0search7

## Quadlet and updates

The included Quadlet definition demonstrates how the web service can be hosted as a container. Podman Quadlet supports declarative systemd-managed containers, and Podman's auto-update mechanism can update images and restart associated units. citeturn0search0turn0search4

## Platform

Podman supports Linux and provides Podman Machine/remote-client workflows for macOS and Windows. The native Chimera node is designed around the Koronos/Linux container environment, while remote clients can manage a Linux Podman node. citeturn0search11turn0search19
