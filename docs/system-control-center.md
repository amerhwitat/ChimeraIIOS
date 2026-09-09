# Chimera System Control Center

The **Chimera System Control Center (CSCC)** is Aurora's unified management surface for system observability, desktop preferences, services, processes, sessions and recovery.

## UI

Open `web/system_control_center.html` from Aurora's dedicated taskbar/dock button. The interface provides Overview, Processes, Services, Performance & KPIs, Settings & Preferences, Desktop & Sessions, Startup and Recovery.

## Telemetry

The contract is `web/system_control_center.json`. KPI records carry `value`, `unit`, `status`, `source`, `timestamp`, `confidence`, and optional detail. This prevents the UI from presenting browser or simulated measurements as native hardware facts.

## Backend boundary

The browser does not execute arbitrary host commands. Optional endpoints under `/api/system/*` may be supplied by an authorized host/session adapter. Process and service lifecycle operations remain disabled unless the backend advertises the corresponding capability. Power/session requests are likewise capability-gated and confirmation-protected.

## Settings

Local preferences use the `chimera.control.*` namespace. Desktop selection continues to use `chimera.desktop.profile`. Native persistence is optional and backend-controlled.

## Desktop integration

The Control Center has a permanent Aurora dock/taskbar launcher. It coexists with the Desktop Switcher and Retro Emulator Center. Linux desktop profiles and Windows profiles remain web/session adapters until a real authorized session backend is present.

## Cross-repository integration

Supporting repositories consume the canonical contract and UI through lightweight `aurora_observability.json` or `chimera_ui_integration.json` manifests. This keeps one source of truth and avoids unsafe duplication of host-management logic.
