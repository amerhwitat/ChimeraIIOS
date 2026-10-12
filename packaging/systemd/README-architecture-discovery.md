# Optional runtime discovery timer

The user-level systemd unit files here let an Aurora session periodically generate a bounded, offline-by-default architecture/ISA candidate report. The timer is weekly and does not require network access. Online scans must be explicitly enabled by invoking the tool with `--online`; the timer intentionally does not do this automatically.

The package must install `chimera_discovery.py` at `~/.local/lib/chimera/tools/architecture_discovery/chimera_discovery.py` and install these units under `~/.config/systemd/user/`. Then enable with:

```sh
systemctl --user daemon-reload
systemctl --user enable --now chimera-architecture-discovery.timer
systemctl --user list-timers chimera-architecture-discovery.timer
```

This unit is a packaging template. Until the installer/package step places the script and unit files in these paths, it is not active. The report is metadata for Aurora's Architecture & Compatibility Research panel, not an executable compatibility backend.
