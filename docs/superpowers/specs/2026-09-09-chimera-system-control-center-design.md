# Chimera System Control Center Design

## Purpose

Create one professional management surface for Aurora Wayland Glass Desktop and the Web UI. It combines desktop preferences, process/service inspection and control, system health KPIs, session switching, startup preferences, and recovery visibility.

## Product name

**Chimera System Control Center (CSCC)**.

## User experience

The application uses a native-looking Aurora glass utility layout: top title bar, left navigation rail, KPI summary cards, dense sortable tables, resource meters, status pills, command/action menus, and confirmation dialogs. It is available from the Aurora taskbar/dock and All Applications launcher.

## Functional sections

1. Overview: CPU, memory, storage, network, uptime, kernel, ISA/N-bit runtime, graphics, cognitive plane, active desktop, and aggregate health.
2. Processes: PID, name, user, CPU, memory, state, start time, priority, command, source, and health; filter/search/sort; stop/terminate when authorized.
3. Services: name, description, state, startup mode, PID, source and health; start/stop/restart/enable/disable when authorized.
4. Performance & KPIs: live CPU/memory/disk/network plus subsystem health with source, timestamp, confidence and status.
5. Settings & Preferences: desktop profile, theme, taskbar behavior, startup applications, notifications, power/session preferences, terminal defaults, network preferences, and safe-lab security mode.
6. Desktop & Sessions: select Aurora/Linux/Windows UI profiles and expose native session status without pretending a web profile is a real OS session.
7. Startup: inspect configured startup applications/services and change them only through an authorized backend.
8. Recovery: surface crash/recovery information and provide reboot/shutdown controls only when a backend advertises them.

## Capability model

The browser requests a capability document. Each management action is enabled only if its capability is true. Browser-only and simulator implementations expose read-only/simulated behavior. Native adapters may implement process/service operations through OS-specific privileged APIs.

## Data model

Processes use: `pid`, `name`, `user`, `cpu_percent`, `memory_percent`, `memory_bytes`, `state`, `start_time`, `priority`, `command`, `source`, `health`.

Services use: `id`, `name`, `description`, `state`, `startup`, `pid`, `source`, `health`, `can_start`, `can_stop`, `can_restart`, `can_enable`, `can_disable`.

KPIs use: `id`, `label`, `value`, `unit`, `status`, `source`, `timestamp`, `confidence`, optional `detail`.

## Actions

Stable IDs are `process.stop`, `process.kill`, `service.start`, `service.stop`, `service.restart`, `service.enable`, `service.disable`, `system.shutdown`, `system.reboot`. All destructive actions require confirmation and must return an explicit success/error result.

## API convention

Optional endpoints: `GET /api/system/overview`, `/processes`, `/services`, `/kpis`, `/settings`; `POST /api/system/action`. Backends may expose equivalent transport while retaining the JSON field names and action IDs.

## Settings

Local preferences are namespaced under `chimera.control.*`; desktop selection remains `chimera.desktop.profile`. Native persistence is opt-in and capability-gated.

## Security boundary

The Web UI never directly executes arbitrary shell commands. It may request a narrowly scoped, authenticated/authorized management action from a host/session adapter. Backend errors, permission denial and unavailable capabilities are rendered as such.
