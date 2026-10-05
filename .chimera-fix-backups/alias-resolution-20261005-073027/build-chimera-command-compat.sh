#!/usr/bin/env bash
set -euo pipefail

# --- CHIMERA COMPILER SELECTION ---
#
# Do not directly reference $CHIMERA_CC while nounset (-u) is enabled.
# Respect an explicitly supplied CC, otherwise select an available
# C compiler automatically.
#
if [[ -n "${CC:-}" ]]; then
    CHIMERA_CC="$CHIMERA_CC"
elif command -v cc >/dev/null 2>&1; then
    CHIMERA_CC="$(command -v cc)"
elif command -v gcc >/dev/null 2>&1; then
    CHIMERA_CC="$(command -v gcc)"
elif command -v clang >/dev/null 2>&1; then
    CHIMERA_CC="$(command -v clang)"
else
    echo "[CHIMERA-CMD][ERROR] No C compiler found." >&2
    echo "[CHIMERA-CMD][ERROR] Install gcc/clang or set CC=/path/to/compiler." >&2
    exit 127
fi

echo "[CHIMERA-CMD] C compiler: $CHIMERA_CC"
# --- END CHIMERA COMPILER SELECTION ---

ROOT="${CHIMERA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

BUILD="$ROOT/build"
SRC="$ROOT/src/chimera-command-compat"
OUT="$ROOT/rootfs"
BIN="$OUT/usr/bin"
SBIN="$OUT/usr/sbin"
LIB="$OUT/usr/lib/chimera"
ETC="$OUT/etc/chimera"
CMDROOT="$ETC/commands"
SHARE="$OUT/usr/share/chimera/commands"
BACKUP="$ROOT/.chimera-fix-backups/command-compat"

JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"

mkdir -p \
    "$SRC" \
    "$BIN" \
    "$SBIN" \
    "$LIB" \
    "$ETC" \
    "$CMDROOT" \
    "$SHARE" \
    "$BACKUP" \
    "$BUILD"

log() {
    printf '[CHIMERA-CMD] %s\n' "$*"
}

warn() {
    printf '[CHIMERA-CMD][WARNING] %s\n' "$*" >&2
}

die() {
    printf '[CHIMERA-CMD][ERROR] %s\n' "$*" >&2
    exit 1
}

backup_once() {
    local src="$1"
    local rel
    local dst

    [[ -e "$src" ]] || return 0

    rel="${src#$ROOT/}"
    rel="${rel//\//__}"
    dst="$BACKUP/$rel"

    if [[ ! -e "$dst" ]]; then
        cp -p -- "$src" "$dst"
        log "Backup: $dst"
    fi
}

###############################################################################
# 1. Native multicall command implementation
###############################################################################

"$CHIMERA_CC" \
    -std=c11 \
    -O2 \
    -Wall \
    -Wextra \
    -Werror \
    "$SRC/chimera-cmd.c" \
    -o "$BIN/chimera-cmd"

chmod 0755 "$BIN/chimera-cmd"

###############################################################################
# 3. Install native command names
###############################################################################

NATIVE_COMMANDS=(
    pwd
    echo
    ls
    cp
    mv
    touch
    mkdir
    rm
    cat
    clear
    whoami
    hostname
    date
    true
    false
)

for command in "${NATIVE_COMMANDS[@]}"; do
    target="$BIN/$command"

    if [[ -e "$target" && ! -L "$target" ]]; then
        backup_once "$target"
        rm -f -- "$target"
    fi

    ln -sfn "chimera-cmd" "$target"
done

###############################################################################
# 4. Arabic aliases
###############################################################################

cat > "$CMDROOT/aliases.ar.json" <<'JSON'
{
  "عرض": "ls",
  "دخول": "cd",
  "موقعي": "pwd",
  "نسخ": "cp",
  "نقل": "mv",
  "حذف": "rm",
  "مجلد": "mkdir",
  "ملف": "touch",
  "اقرأ": "cat",
  "مسح": "clear",
  "ابحث": "find",
  "فتش": "grep",
  "عمليات": "ps",
  "انهاء": "kill",
  "اربط": "mount",
  "افصل": "umount",
  "إعادة_تشغيل": "reboot",
  "إيقاف": "shutdown",
  "مساعدة": "help",
  "السجل": "history",
  "دليل": "man",
  "صلاحيات": "chmod",
  "مالك": "chown",
  "مساحة": "df",
  "حجم": "du",
  "مراقبة": "top",
  "هوية": "whoami",
  "اسم_الجهاز": "hostname",
  "تاريخ": "date",
  "نسخة": "uname",
  "حالة": "status",
  "تشغيل": "start",
  "إيقاف_خدمة": "stop",
  "إعادة_تشغيل_خدمة": "restart",
  "شبكة": "ip",
  "اتصال": "ping",
  "مسارات": "route",
  "منافذ": "ss",
  "ملفات_مفتوحة": "lsof",
  "ذاكرة": "free",
  "قرص": "lsblk",
  "أرشفة": "tar",
  "ضغط": "gzip",
  "فك_الضغط": "gunzip",
  "اتصال_آمن": "ssh",
  "نسخ_آمن": "scp",
  "مقارنة": "diff",
  "فرز": "sort",
  "رأس": "head",
  "ذيل": "tail",
  "قص": "cut",
  "استبدال": "sed",
  "تحويل": "awk"
}
JSON

###############################################################################
# 5. Command registry
###############################################################################

cat > "$CMDROOT/registry.tsv" <<'REGISTRY'
# command	arabic	mode	implementation	source
ls	عرض	native	chimera-cmd	SS64/Linux
cd	دخول	shell	cd	SS64/Linux
pwd	موقعي	native	chimera-cmd	SS64/Linux
cp	نسخ	native	chimera-cmd	SS64/Linux
mv	نقل	native	chimera-cmd	SS64/Linux
rm	حذف	native	chimera-cmd	SS64/Linux
mkdir	مجلد	native	chimera-cmd	SS64/Linux
touch	ملف	native	chimera-cmd	SS64/Linux
cat	اقرأ	native	chimera-cmd	SS64/Linux
clear	مسح	native	chimera-cmd	SS64/Linux
find	ابحث	compat	find	SS64/Linux
grep	فتش	compat	grep	SS64/Linux
ps	عمليات	compat	ps	SS64/Linux
kill	انهاء	compat	kill	SS64/Linux
mount	اربط	compat	mount	SS64/Linux
umount	افصل	compat	umount	SS64/Linux
chmod	صلاحيات	compat	chmod	SS64/Linux
chown	مالك	compat	chown	SS64/Linux
df	مساحة	compat	df	SS64/Linux
du	حجم	compat	du	SS64/Linux
top	مراقبة	compat	top	SS64/Linux
tar	أرشفة	compat	tar	SS64/Linux
gzip	ضغط	compat	gzip	SS64/Linux
ssh	اتصال_آمن	compat	ssh	SS64/Linux
scp	نسخ_آمن	compat	scp	SS64/Linux
dir	عرض	windows	cmd:dir	SS64/Windows
copy	نسخ	windows	cmd:copy	SS64/Windows
del	حذف	windows	cmd:del	SS64/Windows
move	نقل	windows	cmd:move	SS64/Windows
cls	مسح	windows	cmd:cls	SS64/Windows
ipconfig	شبكة_ويندوز	windows	ipconfig.exe	SS64/Windows
tasklist	قائمة_المهام	windows	tasklist.exe	SS64/Windows
taskkill	إنهاء_مهمة	windows	taskkill.exe	SS64/Windows
systeminfo	معلومات_النظام	windows	systeminfo.exe	SS64/Windows
where	أين	windows	where.exe	SS64/Windows
Get-Command	احصل_على_الأوامر	powershell	powershell:Get-Command	SS64/PowerShell
Get-ChildItem	استعرض_العناصر	powershell	powershell:Get-ChildItem	SS64/PowerShell
Get-Process	احصل_على_العمليات	powershell	powershell:Get-Process	SS64/PowerShell
Get-Service	احصل_على_الخدمات	powershell	powershell:Get-Service	SS64/PowerShell
Get-Location	احصل_على_الموقع	powershell	powershell:Get-Location	SS64/PowerShell
brew	حزم_ماك	macos	brew	SS64/macOS
xattr	خصائص_ماك	macos	xattr	SS64/macOS
xcrun	أدوات_ماك	macos	xcrun	SS64/macOS
xcode-select	اختيار_إكس_كود	macos	xcode-select	SS64/macOS
open	فتح	macos	open	SS64/macOS
REGISTRY

###############################################################################
# 6. Native/compatibility modes
###############################################################################

cat > "$CMDROOT/modes.conf" <<'MODES'
# Chimera II Command Compatibility Framework

CHIMERA_MODE=native

# Valid values:
#
# native
# linux
# posix
# bash
# zsh
# macos
# windows
# cmd
# powershell
#
# Explicit mode has priority over automatic detection.

AUTO_DETECT=1

LINUX_RUNTIME=
MACOS_RUNTIME=
WINDOWS_RUNTIME=
POWERSHELL_RUNTIME=
CMD_RUNTIME=
MODES

###############################################################################
# 7. Executable-format detector
###############################################################################

cat > "$BIN/chimera-exec" <<'EXEC'
#!/usr/bin/env bash
set -euo pipefail

file="${1:-}"

if [[ -z "$file" ]]; then
    echo "usage: chimera-exec PROGRAM [ARGS...]" >&2
    exit 2
fi

if [[ ! -e "$file" ]]; then
    command -v "$file" >/dev/null 2>&1 || {
        echo "chimera-exec: command not found: $file" >&2
        exit 127
    }

    file="$(command -v "$file")"
fi

detect_format() {
    local f="$1"
    local magic

    magic="$(dd if="$f" bs=1 count=4 2>/dev/null | od -An -tx1 | tr -d ' \n')"

    case "$magic" in
        7f454c46)
            echo ELF
            ;;
        4d5a*)
            echo PE
            ;;
        cffaedfe|cffaedfe)
            echo MACHO64
            ;;
        feedface|feedfacf|cefaedfe|cffaedfe)
            echo MACHO
            ;;
        2321*)
            echo SCRIPT
            ;;
        *)
            if head -c 2 "$f" 2>/dev/null | grep -q '^#!'; then
                echo SCRIPT
            else
                echo UNKNOWN
            fi
            ;;
    esac
}

format="$(detect_format "$file")"

case "$format" in

    ELF)
        exec "$file" "${@:2}"
        ;;

    SCRIPT)
        exec "$file" "${@:2}"
        ;;

    PE)
        if [[ -n "${CHIMERA_WINDOWS_RUNTIME:-}" ]] &&
           command -v "${CHIMERA_WINDOWS_RUNTIME}" >/dev/null 2>&1; then
            exec "${CHIMERA_WINDOWS_RUNTIME}" "$file" "${@:2}"
        fi

        echo "Chimera II: PE/Windows executable detected." >&2
        echo "No Windows compatibility runtime is configured." >&2
        echo "Set CHIMERA_WINDOWS_RUNTIME to a supported runtime." >&2
        exit 126
        ;;

    MACHO|MACHO64)
        if [[ -n "${CHIMERA_MACOS_RUNTIME:-}" ]] &&
           command -v "${CHIMERA_MACOS_RUNTIME}" >/dev/null 2>&1; then
            exec "${CHIMERA_MACOS_RUNTIME}" "$file" "${@:2}"
        fi

        echo "Chimera II: Mach-O/macOS executable detected." >&2
        echo "No macOS compatibility runtime is configured." >&2
        exit 126
        ;;

    *)
        echo "Chimera II: unsupported executable format: $file" >&2
        exit 126
        ;;

esac
EXEC

chmod 0755 "$BIN/chimera-exec"

###############################################################################
# 8. Main command dispatcher
###############################################################################

cat > "$BIN/chimera" <<'DISPATCH'
#!/usr/bin/env bash
set -euo pipefail

# CHIMERA_COMMAND_ROOT may point to the staged rootfs during build tests.
# Installed systems normally use /etc/chimera/commands.
CONF="${CHIMERA_COMMAND_ROOT:-/etc/chimera/commands}"
REGISTRY="$CONF/registry.tsv"

usage() {
    cat <<'EOF'
Chimera II Command Framework

Usage:
  chimera <command> [arguments...]
  chimera --mode MODE <command> [arguments...]
  chimera help <command>
  chimera native <command> [arguments...]
  chimera compat MODE <command> [arguments...]
  chimera exec PROGRAM [arguments...]

Modes:
  native
  linux
  posix
  bash
  zsh
  macos
  windows
  cmd
  powershell
EOF
}

find_alias() {
    local name="$1"

    [[ -f "$CONF/aliases.ar.json" ]] || return 1

    python3 - "$CONF/aliases.ar.json" "$name" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

name = sys.argv[2]

for ar, command in data.items():
    if ar == name:
        print(command)
        raise SystemExit(0)

raise SystemExit(1)
PY
}

lookup_mode() {
    local command="$1"

    awk -F '\t' -v c="$command" '
        $0 !~ /^#/ && $1 == c {
            print $3
            exit
        }
    ' "$REGISTRY" 2>/dev/null || true
}

lookup_impl() {
    local command="$1"

    awk -F '\t' -v c="$command" '
        $0 !~ /^#/ && $1 == c {
            print $4
            exit
        }
    ' "$REGISTRY" 2>/dev/null || true
}

run_native() {
    local command="$1"
    shift

    case "$command" in
        cd)
            builtin cd -- "$@"
            ;;
        *)
            local root_prefix="${CHIMERA_ROOT_PREFIX:-}"

            if [[ -x "${root_prefix}/usr/bin/$command" ]]; then
                exec "${root_prefix}/usr/bin/$command" "$@"
            fi

            if command -v "$command" >/dev/null 2>&1; then
                exec "$command" "$@"
            fi

            echo "chimera: native command unavailable: $command" >&2
            return 127
            ;;
    esac
}

run_compat() {
    local mode="$1"
    local command="$2"
    shift 2

    case "$mode" in

        linux|posix|bash|zsh)
            exec "$command" "$@"
            ;;

        macos)
            if command -v "$command" >/dev/null 2>&1; then
                exec "$command" "$@"
            fi

            echo "chimera: macOS command unavailable: $command" >&2
            echo "Install/configure a macOS compatibility runtime." >&2
            return 126
            ;;

        windows|cmd)
            if [[ -n "${CHIMERA_CMD_RUNTIME:-}" ]] &&
               command -v "${CHIMERA_CMD_RUNTIME}" >/dev/null 2>&1; then
                exec "${CHIMERA_CMD_RUNTIME}" /c "$command" "$@"
            fi

            echo "chimera: Windows CMD runtime unavailable." >&2
            return 126
            ;;

        powershell)
            if [[ -n "${CHIMERA_POWERSHELL_RUNTIME:-}" ]] &&
               command -v "${CHIMERA_POWERSHELL_RUNTIME}" >/dev/null 2>&1; then

                local joined
                printf -v joined '%q ' "$command" "$@"

                exec "${CHIMERA_POWERSHELL_RUNTIME}" \
                    -NoLogo \
                    -NoProfile \
                    -Command \
                    "$joined"
            fi

            echo "chimera: PowerShell runtime unavailable." >&2
            return 126
            ;;

        *)
            echo "chimera: unknown mode: $mode" >&2
            return 2
            ;;
    esac
}

if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

mode="${CHIMERA_MODE:-auto}"

if [[ "$1" == "--mode" ]]; then
    [[ $# -ge 3 ]] || {
        usage
        exit 2
    }

    mode="$2"
    shift 2
fi

case "$1" in

    help)
        if [[ $# -eq 1 ]]; then
            usage
            exit 0
        fi

        command="$2"

        if ar="$(find_alias "$command" 2>/dev/null)"; then
            echo "$command -> $ar"
        fi

        echo
        echo "Command: $command"
        echo "Mode: $(lookup_mode "$command")"
        echo "Implementation: $(lookup_impl "$command")"
        echo "Reference: SS64 command registry"
        exit 0
        ;;

    native)
        shift
        [[ $# -gt 0 ]] || {
            echo "usage: chimera native COMMAND [ARGS...]" >&2
            exit 2
        }
        run_native "$@"
        ;;

    compat)
        [[ $# -ge 3 ]] || {
            echo "usage: chimera compat MODE COMMAND [ARGS...]" >&2
            exit 2
        }

        compat_mode="$2"
        command="$3"
        shift 3

        run_compat "$compat_mode" "$command" "$@"
        ;;

    exec)
        shift
        exec /usr/bin/chimera-exec "$@"
        ;;

    *)
        ;;
esac

command="$1"
shift

# Arabic command → canonical command.
if ar="$(find_alias "$command" 2>/dev/null)"; then
    command="$ar"
fi

declared_mode="$(lookup_mode "$command")"

if [[ "$mode" == "auto" ]]; then
    mode="$declared_mode"

    [[ -n "$mode" ]] || mode="native"
fi

case "$mode" in
    native)
        run_native "$command" "$@"
        ;;

    shell)
        exec "$command" "$@"
        ;;

    linux|posix|bash|zsh|macos|windows|cmd|powershell)
        run_compat "$mode" "$command" "$@"
        ;;

    *)
        echo "chimera: unsupported execution mode: $mode" >&2
        exit 2
        ;;
esac
DISPATCH

chmod 0755 "$BIN/chimera"

###############################################################################
# 9. Shell integration
###############################################################################

mkdir -p "$OUT/etc/profile.d"

cat > "$OUT/etc/profile.d/chimera-command-compat.sh" <<'PROFILE'
# Chimera II Command Compatibility Framework

export CHIMERA_COMMAND_ROOT="/etc/chimera/commands"
export CHIMERA_MODE="${CHIMERA_MODE:-native}"

chimera-mode() {
    export CHIMERA_MODE="$1"
    printf 'CHIMERA_MODE=%s\n' "$CHIMERA_MODE"
}

chimera-native() {
    CHIMERA_MODE=native /usr/bin/chimera "$@"
}

chimera-linux() {
    CHIMERA_MODE=linux /usr/bin/chimera "$@"
}

chimera-macos() {
    CHIMERA_MODE=macos /usr/bin/chimera "$@"
}

chimera-windows() {
    CHIMERA_MODE=windows /usr/bin/chimera "$@"
}

chimera-powershell() {
    CHIMERA_MODE=powershell /usr/bin/chimera "$@"
}

chimera-exec() {
    /usr/bin/chimera-exec "$@"
}

# Arabic shell functions.
عرض()       { /usr/bin/chimera ls "$@"; }
دخول()      { builtin cd "$@"; }
موقعي()     { /usr/bin/chimera pwd "$@"; }
نسخ()       { /usr/bin/chimera cp "$@"; }
نقل()       { /usr/bin/chimera mv "$@"; }
حذف()       { /usr/bin/chimera rm "$@"; }
مجلد()      { /usr/bin/chimera mkdir "$@"; }
ملف()       { /usr/bin/chimera touch "$@"; }
اقرأ()      { /usr/bin/chimera cat "$@"; }
مسح()       { /usr/bin/chimera clear "$@"; }
هوية()      { /usr/bin/chimera whoami "$@"; }
اسم_الجهاز(){ /usr/bin/chimera hostname "$@"; }
تاريخ()     { /usr/bin/chimera date "$@"; }
مساعدة()    { /usr/bin/chimera help "$@"; }
دليل()      { /usr/bin/chimera help "$@"; }
شبكة()      { /usr/bin/chimera ip "$@"; }
اتصال()     { /usr/bin/chimera ping "$@"; }
مساحة()     { /usr/bin/chimera df "$@"; }
حجم()       { /usr/bin/chimera du "$@"; }
مراقبة()    { /usr/bin/chimera top "$@"; }
فتش()       { /usr/bin/chimera grep "$@"; }
ابحث()      { /usr/bin/chimera find "$@"; }
عمليات()    { /usr/bin/chimera ps "$@"; }
انهاء()     { /usr/bin/chimera kill "$@"; }
صلاحيات()   { /usr/bin/chimera chmod "$@"; }
مالك()      { /usr/bin/chimera chown "$@"; }
أرشفة()     { /usr/bin/chimera tar "$@"; }
ضغط()       { /usr/bin/chimera gzip "$@"; }
اتصال_آمن() { /usr/bin/chimera ssh "$@"; }
نسخ_آمن()   { /usr/bin/chimera scp "$@"; }
مقارنة()    { /usr/bin/chimera diff "$@"; }
فرز()       { /usr/bin/chimera sort "$@"; }
رأس()       { /usr/bin/chimera head "$@"; }
ذيل()       { /usr/bin/chimera tail "$@"; }
قص()        { /usr/bin/chimera cut "$@"; }
استبدال()   { /usr/bin/chimera sed "$@"; }
تحويل()     { /usr/bin/chimera awk "$@"; }
PROFILE

###############################################################################
# 10. Documentation / runtime contract
###############################################################################

cat > "$SHARE/README.md" <<'DOC'
# Chimera II Command Compatibility Framework

Chimera provides four layers:

1. Chimera-native commands
2. POSIX/Linux command compatibility
3. Windows CMD/PowerShell compatibility
4. macOS command compatibility

SS64 is treated as a command-reference source, not as a binary distribution.

Native binaries are compiled by the Chimera builder.

Foreign executable formats are detected before execution:

ELF   -> native/Linux runtime
PE    -> Windows compatibility runtime
Mach-O -> macOS compatibility runtime
script -> interpreter from shebang

A missing compatibility runtime is a controlled error and never silently
pretends that the foreign executable is a native Chimera executable.

Arabic command names are exposed through `/etc/profile.d/chimera-command-compat.sh`.

Examples:

    عرض
    موقعي
    نسخ file1 file2
    حذف file
    مجلد test
    دليل ls

Explicit modes:

    CHIMERA_MODE=native chimera ls
    CHIMERA_MODE=linux chimera grep foo file
    CHIMERA_MODE=macos chimera open .
    CHIMERA_MODE=windows chimera dir
    CHIMERA_MODE=powershell chimera Get-Process

Executable dispatch:

    chimera exec ./program

This layer is intentionally independent from Koronos.
DOC

###############################################################################
# 11. Runtime environment configuration
###############################################################################

cat > "$ETC/runtime.conf" <<'RUNTIME'
# Chimera II external compatibility runtimes.
#
# Leave empty until the corresponding runtime is installed.

CHIMERA_LINUX_RUNTIME=""
CHIMERA_MACOS_RUNTIME=""
CHIMERA_WINDOWS_RUNTIME=""
CHIMERA_CMD_RUNTIME=""
CHIMERA_POWERSHELL_RUNTIME=""
RUNTIME

###############################################################################
# 12. Validation
###############################################################################

log "Validating generated shell files..."

bash -n "$BIN/chimera"
bash -n "$BIN/chimera-exec"
bash -n "$OUT/etc/profile.d/chimera-command-compat.sh"

log "Testing native command binary..."

"$BIN/chimera-cmd"

for command in "${NATIVE_COMMANDS[@]}"; do
    [[ -x "$BIN/$command" ]] || die \
        "Native command missing: $command"
done

log "Testing command dispatcher against staged rootfs..."

CHIMERA_COMMAND_ROOT="$CMDROOT" \
CHIMERA_ROOT_PREFIX="$OUT" \
    "$BIN/chimera" help ls

CHIMERA_COMMAND_ROOT="$CMDROOT" \
CHIMERA_ROOT_PREFIX="$OUT" \
    "$BIN/chimera" help عرض

###############################################################################
# Verify registry resolution
###############################################################################

log "Verifying registry resolution..."

registry_mode="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help ls |
        awk -F': ' '/^Mode:/ {print $2}'
)"

registry_impl="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help ls |
        awk -F': ' '/^Implementation:/ {print $2}'
)"

[[ -n "$registry_mode" ]] || {
    die "Registry mode lookup returned empty result."
}

[[ -n "$registry_impl" ]] || {
    die "Registry implementation lookup returned empty result."
}

[[ "$registry_mode" == "native" ]] || {
    die "ls must resolve to native mode, got: $registry_mode"
}

log "Registry resolution: ls -> $registry_mode / $registry_impl"

###############################################################################
# Verify Arabic resolution
###############################################################################

arabic_resolution="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help عرض
)"

grep -q '^عرض -> ls$' <<<"$arabic_resolution" || {
    die "Arabic alias resolution failed for عرض -> ls"
}

log "Arabic resolution: عرض -> ls"

log "Testing Arabic registry..."

python3 - "$CMDROOT/aliases.ar.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

required = {
    "عرض",
    "دخول",
    "موقعي",
    "نسخ",
    "نقل",
    "حذف",
    "مجلد",
    "ملف",
    "اقرأ",
    "مسح",
    "مساعدة",
}

missing = required - set(data)

if missing:
    print("Missing Arabic aliases:", ", ".join(sorted(missing)))
    raise SystemExit(1)

print("Arabic aliases:", len(data))
PY

###############################################################################
# 13. Build manifest
###############################################################################

cat > "$BUILD/chimera-command-compat.manifest" <<EOF
CHIMERA_COMMAND_COMPAT=1
NATIVE_BINARY=$BIN/chimera-cmd
DISPATCHER=$BIN/chimera
EXEC_FORMAT_DISPATCHER=$BIN/chimera-exec
REGISTRY=$CMDROOT/registry.tsv
ARABIC_ALIASES=$CMDROOT/aliases.ar.json
MODE_CONFIG=$CMDROOT/modes.conf
RUNTIME_CONFIG=$ETC/runtime.conf
EOF

log "Command compatibility subsystem installed."

printf '\n'
printf '%s\n' '============================================================'
printf '%s\n' ' Chimera II Command Compatibility Framework'
printf '%s\n' '============================================================'
printf 'Native commands : %d\n' "${#NATIVE_COMMANDS[@]}"
printf 'Arabic aliases   : '
python3 - "$CMDROOT/aliases.ar.json" <<'PY'
import json,sys
print(len(json.load(open(sys.argv[1],encoding="utf-8"))))
PY
printf 'Registry         : %s\n' "$CMDROOT/registry.tsv"
printf 'Dispatcher       : %s\n' "$BIN/chimera"
printf 'Exec dispatcher  : %s\n' "$BIN/chimera-exec"
printf 'Manifest         : %s\n' "$BUILD/chimera-command-compat.manifest"
printf '%s\n' '============================================================'
