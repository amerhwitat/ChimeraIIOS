#!/usr/bin/env bash
# Chimera II OS shell integration: English + Arabic command names.
export CHIMERA_LANG="${CHIMERA_LANG:-ar}"
export CHIMERA_COMMAND_CATALOG="${CHIMERA_COMMAND_CATALOG:-/usr/share/chimera/commands/chimera-command-list.json}"
export CHIMERA_ARABIC_CATALOG="${CHIMERA_ARABIC_CATALOG:-/usr/share/chimera/commands/chimera-arabic.json}"
export LANG="${LANG:-C.UTF-8}"
export LC_CTYPE="${LC_CTYPE:-C.UTF-8}"

if command -v chimera >/dev/null 2>&1; then
  alias مساعدة='chimera help --lang ar'
  alias الأوامر='chimera commands --lang ar'
  alias الأوامر_الأصلية='chimera native --lang ar'
  alias ابحث='chimera search --lang ar'
  alias أين='chimera which --lang ar'
  alias معلومات_شيميرا='chimera info --lang ar'
  alias تشخيص_شيميرا='chimera doctor --lang ar'
  alias طرفية_شيميرا='chimera shell --lang ar'
fi
alias قائمة='ls'
alias مجلد='ls'
alias انتقل='cd'
alias المسار='pwd'
alias نسخ='cp'
alias نقل='mv'
alias حذف='rm'
alias أنشئ_مجلد='mkdir'
alias احذف_مجلد='rmdir'
alias اعرض='cat'
alias ابحث_نصي='grep'
alias ابحث_ملف='find'
alias رتّب='sort'
alias مسح='clear'
alias السجل='history'
alias دليل='man'
alias العمليات='ps'
alias مراقبة='top'
alias مساحة='df'
alias الذاكرة='free'
alias صلاحيات='chmod'
alias مالك='chown'
alias كلمة_المرور='passwd'
alias من_أنا='whoami'
alias معلومات_النظام='uname'
alias الشبكة='ip'
alias اختبر_الشبكة='ping'
alias اتصال_آمن='ssh'
alias تنزيل='wget'
alias أرشيف='tar'
alias بناء='make'
alias بايثون='python3'
alias جافا='java'
alias نود='node'
alias دوكر='docker'

alias أوامر_سس64='chimera ss64 --lang ar'
alias مساعدة_سس64='chimera help --lang ar'
نفّذ() { command chimera run --lang ar "$@"; }
شغّل() { command chimera run --lang ar "$@"; }
شغل() { command chimera run --lang ar "$@"; }
