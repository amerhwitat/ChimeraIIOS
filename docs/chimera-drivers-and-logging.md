# Chimera II OS Driver Acquisition, Updates, and /var/log/mesgs

## Runtime surfaces

The same driver manager is exposed in three environments:

- Installer: inventory/search runs after the installer environment starts and network tools are available.
- Live CD: hardware inventory is collected from sysfs and the cached PCI ID database can be refreshed.
- Installed Aurora: **Chimera II Driver Center** launches the search/update workflow and the Aurora system monitor exposes driver state.

## Driver acquisition model

The manager discovers PCI and USB IDs, refreshes PCI identification metadata, and uses an extensible repository registry.

Configured sources include Linux firmware, Debian/Ubuntu/Fedora/Arch/openSUSE/FreeBSD source/package locations, LVFS/fwupd, and the PCI ID database. Vendor repositories can be added under /etc/chimera/drivers.d/.

Native Chimera artifacts (.chm-driver, .chmfw) and firmware are eligible for installation. Foreign formats such as Linux .ko, Windows .sys/.inf, and macOS .kext/.dext are not treated as native executable code. They are quarantined until a Chimera compatibility provider validates or translates them.

The policy deliberately separates hardware identification, acquisition, verification, and activation. This follows the same general separation used by Linux firmware loading, where drivers request firmware from defined search paths and can load it asynchronously.

## Security

- HTTPS is required for configured remote sources.
- SHA-256 verification is supported by policy.
- Unrecognized/foreign artifacts are quarantined.
- Untrusted driver code is never executed automatically.
- Vendor repositories are opt-in extensions rather than unrestricted web crawling.
- Firmware/device update mechanisms must perform their own device-specific validation.

## Logging

The primary runtime log is /var/log/mesgs.

Compatibility path: /var/log/messages -> /var/log/mesgs

Archives: /var/log/mesgs/archive/

Configuration: /etc/chimera/logging.conf

Defaults rotate every 24 hours or when the file reaches 50 MiB, keep 30 archives, and gzip archives when gzip is available. Users can change ROTATE_SECONDS, MAX_BYTES, KEEP_ARCHIVES, and COMPRESS, then invoke chimera-logrotate for immediate rotation.

The log daemon and timer are installed as system services when systemd is present. Non-systemd deployments can invoke the same utilities from the Kore/native service manager.

## External metadata and firmware

The PCI ID project publishes daily compressed snapshots for device identification. LVFS/fwupd provides vendor firmware using standardized metadata/archive delivery. Debian also maintains firmware packages, including a dedicated non-free-firmware component.

These sources are used as acquisition/metadata inputs; their contents are not assumed to be executable by the Chimera kernel.
