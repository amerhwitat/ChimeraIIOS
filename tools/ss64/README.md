# SS64 → Arabic Chimera command aliases

`chimera-ss64-arabic-aliases.py` indexes SS64 command lists and generates:

- `manifest.json` — command metadata and source URLs
- `<shell>.json` — structured command records
- `<shell>.bash_aliases` — short Arabic aliases

The generator records command names and short Arabic labels; it does **not** copy SS64 article text. SS64 remains the source reference. The Linux/Bash index contains the command list and descriptions; SS64's alias documentation explains normal Bash alias behavior and startup loading. See https://ss64.com/bash/ and https://ss64.com/bash/alias.html.

## Generate

```bash
python3 tools/ss64/chimera-ss64-arabic-aliases.py
```

Offline generation from saved index pages:

```bash
python3 tools/ss64/chimera-ss64-arabic-aliases.py --offline-dir /path/to/indexes --shell bash
```

## Install

```bash
bash tools/ss64/install-ss64-arabic-aliases.sh
```

Only the Bash/Linux alias set should be loaded into the default Chimera Linux shell. Windows CMD and PowerShell records are retained as compatibility metadata and should not be sourced as Bash aliases.

Examples:

```text
عرض       -> ls
دخول      -> cd
مسار      -> pwd
نسخ       -> cp
نقل       -> mv
حذف       -> rm
ابحث      -> grep
اعثر      -> find
مساعدة    -> help
دليل      -> man
تنزيل     -> wget
اتصال_آمن -> ssh
```

These are convenience aliases; the original command names remain available.
