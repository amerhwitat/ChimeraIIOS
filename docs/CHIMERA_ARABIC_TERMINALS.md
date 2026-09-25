# Chimera II OS — Arabic Command Console, Shells and Free Terminals

## Command catalog

The unified catalog is designed to expose the command families indexed by SS64 (Linux/Bash, macOS, Windows CMD, PowerShell, VBScript and SQL Server) without copying SS64 page prose. SS64's root reference currently links Linux, macOS, CMD, PowerShell, VBScript, Tools and Passwords; the PowerShell index also documents CMD interoperability. citeturn0search1turn0search9

Use:

```bash
chimera commands
chimera native
chimera search TERM
chimera help COMMAND
chimera which COMMAND
chimera exec COMMAND ...
chimera info
chimera doctor
```

## العربية

The shell integration is additive: English/POSIX commands remain valid, while Arabic aliases are added.

```bash
مساعدة
الأوامر
الأوامر_الأصلية
ابحث TERM
أين COMMAND

قائمة
انتقل DIR
نسخ SOURCE DEST
نقل SOURCE DEST
حذف FILE
اعرض FILE
ابحث_نصي TERM
ابحث_ملف PATH
مسح
السجل
دليل COMMAND
العمليات
مساحة
الذاكرة
صلاحيات MODE FILE
كلمة_المرور
من_أنا
معلومات_النظام
الشبكة
اختبر_الشبكة HOST
اتصال_آمن HOST
تنزيل URL
أرشيف FILE
بناء
بايثون
جافا
نود
دوكر
```

The localized command catalog displays an Arabic label followed by the exact original command in brackets. This preserves script compatibility and avoids silently changing POSIX/CMD/PowerShell semantics.

## Open-source terminals

The registry covers free/open-source terminal emulators including Foot, Alacritty, Kitty, WezTerm, Ptyxis, GNOME Terminal, Konsole, XFCE Terminal, Terminator and XTerm.

Current upstream evidence:
- Alacritty: Apache-2.0 and cross-platform/OpenGL. citeturn2search1turn1search5
- Kitty: GPL-3.0 and GPU-based/cross-platform. citeturn2search3turn2search8
- WezTerm: MIT and GPU-accelerated terminal/multiplexer. citeturn1search0turn1search8
- Foot: MIT, lightweight and Wayland-native. citeturn0search3
- Ptyxis: GPL-3.0-or-later, GTK4/VTE and container-aware. citeturn0search0
- Rio: MIT, hardware-accelerated and GPU-oriented. citeturn2search0
- Ghostty: MIT and GPU/native-UI oriented; it is recorded as an upstream option but is not forced into the Ubuntu package install if the configured repository does not provide it. citeturn1search3turn1search12

The installer checks package availability one terminal at a time. A missing package is skipped, so a single terminal cannot break the ISO. XDG application entries are created only when the corresponding executable exists; they therefore appear in the Aurora applications panel without deliberately creating broken launchers.

## Aurora Wayland Glass artwork

The build now accepts the supplied Aurora image through `CHIMERA_AURORA_ASSET` or repository asset paths:

```bash
export CHIMERA_AURORA_ASSET=/path/to/Aurora-Wayland-Glass-Desktop.png
sudo bash ./build-chimera-iso.sh --clean-state
```

When supplied, the image is staged to:

- GRUB main menu
- Jasper boot manager
- Spit Fire boot menu
- installer background
- installer/library background
- Aurora desktop background

The existing SVG backgrounds remain as deterministic fallbacks for unattended builds.

## Important packaging rule

Chimera records upstream terminal source repositories and licenses but does not copy third-party source code into the repository merely to create the application-panel entries. This keeps the ISO build auditable and allows future source-build profiles to fetch the selected upstream project under its own license.

## Deep SS64 integration

The comprehensive image now runs the deep SS64 indexer during the Docker build. It recursively follows same-site command-reference pages for Linux/Bash, macOS, Windows CMD, PowerShell, VBScript, SQL Server, Access and SS64 Tools, storing command names and source URLs in ss64-command-catalog.json. The SS64 root currently links Linux, macOS, CMD, PowerShell, ASCII, VBScript, Tools and Passwords; Passwords/ASCII are reference material rather than executable command namespaces. citeturn1search5turn1search2

The Chimera shell exposes the result with:

```bash
chimera ss64
chimera ss64 grep
أوامر_سس64
نفّذ grep pattern file
شغّل ip addr
```

Linux commands are backed by Ubuntu/Debian binaries where packages are available. The provider installer is intentionally package-by-package and non-fatal for unavailable packages. Platform-specific CMD/PowerShell/macOS/VBScript commands are registered for compatibility and dispatch; Chimera does not falsely claim that a Windows-only executable or macOS-only system service is natively implemented on Linux. PowerShell itself can invoke standard external CMD commands, while VBScript is normally hosted by Windows Script Host on Windows. citeturn0search1turn1search0

## Background image

A compact offline copy of the supplied Aurora artwork is embedded in the repository as system/branding/aurora-default.jpg.base64. The build uses it whenever CHIMERA_AURORA_ASSET is not supplied, so the ISO remains reproducible without requiring the original upload to be present.

The default is applied to GRUB, Jasper, Spit Fire, installer/library and Aurora desktop surfaces. GRUB supports a background_image command for its active terminal. citeturn2search12

Change at build time:

```bash
export CHIMERA_AURORA_ASSET=/path/to/new-background.png
sudo bash ./build-chimera-iso.sh --clean-state
```

Change after installation:

```bash
sudo chimera-background set /path/to/new-background.jpg
chimera-background show
sudo chimera-background reset
```
