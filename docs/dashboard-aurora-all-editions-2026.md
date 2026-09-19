# Chimera II OS Smart Dashboard — Aurora Wayland Glass

The dashboard is a common observability surface for Desktop, Server, Mobile, Edge, IoT and CVEL editions.

## Edition profiles

Each edition receives a profile in `dashboard/edition_profiles.json`. Profiles select panels and refresh intervals while retaining the same KPI schema.

| Edition | Primary dashboard focus |
|---|---|
| Desktop | interactive desktop, resource, network, services and AI health |
| Server | resource, services, routing, security, peers and AI health |
| Mobile | battery-friendly resource, network, services and security views |
| Edge | resource, network/routing, security, peers and AI views |
| IoT | low-overhead resource, network, services, security and peers |
| CVEL | virtualized resource, routing, security, peers and AI views |

## KPI model

The registry includes CPU and memory utilization, storage, network rates/errors/drops, process count, uptime, load, PSI contention where available, boot time, service failures, security advisories, pending updates, routes, peers and AI-runtime activity.

## Safety and privacy

The dashboard is local-first and read-only by default. Remote control is disabled and privileged operations require explicit confirmation elsewhere in the OS. Dashboard history is bounded and local by default.

## Portable collection

`tools/dashboard/chimera_dashboard.py` provides a read-only JSON snapshot helper. It is intentionally conservative: unavailable platform counters are reported as zero rather than guessed, and it does not change routing, services, filesystems or security state.

## Observability alignment

Chimera's KPI naming is designed to map to OpenTelemetry system observability concepts. OpenTelemetry currently documents stable metrics and a mature telemetry lifecycle, while its Linux host packaging remains explicitly described as early-stage and not production-ready; Chimera therefore treats external OpenTelemetry components as optional integrations rather than mandatory OS dependencies.

## Verification

The CMake graph contains a dedicated `chimera_dashboard` test and installs the shared dashboard registry, edition profiles, Aurora configuration, native header and portable dashboard utility. Full native builds must still be verified by the repository CI/toolchain matrix for each target architecture.
