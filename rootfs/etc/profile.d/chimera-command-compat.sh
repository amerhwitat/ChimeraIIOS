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
