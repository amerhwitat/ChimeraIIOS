# Aurora Service Center

Aurora's Services center is a policy client of Kore. It must never directly start privileged processes or edit service state files.

## Views

- Installed
- Available
- Running
- Stopped
- Failed
- Startup
- Dependencies
- Logs
- Enterprise Services

## Operations

`list_services`, `start_service`, `stop_service`, `restart_service`, `enable_service`, and `disable_service` are requests sent through the native Kore IPC boundary. Kore validates authorization, dependencies, hardware requirements, and security policy before changing state.

## Recovery behavior

A failed optional service is isolated and reported. A failed critical service is attributed to the boot journal and may route the machine to Recovery or Safe Mode according to the boot policy. Aurora itself must remain usable whenever a safe graphical fallback exists.

## Installer relationship

Aurora reads the same `config/services/service-registry.json`, `service-profiles.json`, `hardware-requirements.json`, and `security-policies.json` definitions that the installer and ISO builder validate.
