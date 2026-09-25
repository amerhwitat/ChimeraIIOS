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
