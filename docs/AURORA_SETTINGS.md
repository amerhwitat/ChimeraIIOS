# Aurora Settings

Aurora Settings is the native Chimera II OS settings surface. It uses a sidebar/detail information architecture inspired by modern desktop settings applications: grouped categories, searchable settings, immediate safe changes, and explicit privilege boundaries.

## Categories

- System
- Bluetooth & devices
- Network & internet
- Personalization
- Apps
- Accounts
- Time & language
- Gaming
- Accessibility
- Privacy & security
- Windows/Linux/macOS compatibility
- System & services
- Drivers & hardware
- Storage
- Developer

The category model is intentionally broader than a single upstream desktop and maps settings to Chimera components such as Koronos, Kore, Spit Fire, Jasper, Spotnik, Nucleus, Hive and Aegis.

## Native command line

`aurora-settings list` lists settings.

`aurora-settings show KEY` reads one setting.

`aurora-settings set KEY VALUE` persists a setting.

`aurora-settings category system` filters a category.

`aurora-settings reset` restores defaults.

`chmctl settings ...` is the system-control gateway to the same settings model.

## Privilege boundary

User preferences are persisted in `~/.config/chimera/settings.conf`. Changes that require hardware, kernel, service, firmware, security, or system-wide privileges are intended to be mediated by Koronos/Aegis rather than allowing the desktop process to bypass policy.

Windows documents a unified Settings application and page-visibility controls; Aurora follows the same architectural idea while using its own native implementation and configuration model.
