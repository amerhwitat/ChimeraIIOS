# Chimera II OS Smart Dashboard — Aurora Wayland Glass

The dashboard is a local-first observability surface shared by Desktop, Server, Mobile, Edge, IoT and CVEL editions.

## KPI groups

- Utilization: CPU, memory, storage, paging.
- Responsiveness: load, CPU/memory/I/O PSI when available, boot time.
- Network: receive/transmit rate, errors, drops, route count, peer count.
- Workload: process counts and AI runtime activity.
- Reliability: failed services and uptime.
- Security: advisory and pending-update counts from the Sentinel planner.

CPU and system metric naming follows OpenTelemetry's system metric conventions where applicable. Linux PSI is used as a contention signal when exposed by the kernel.

## Edition behavior

The same dashboard model is used on every edition. The collector enables metrics according to platform capabilities; unavailable metrics are reported as `unknown` rather than fabricated.

Aurora Wayland Glass provides adaptive cards, historical sparklines, drill-down views and snapshot export. Remote export and privileged control are opt-in and confirmation-gated.

## Safety

The dashboard is observational by default. It does not automatically kill processes, alter routes, change firewall rules, patch the kernel, or modify services. Remediation remains under the existing Sentinel policy and explicit authorization model.
