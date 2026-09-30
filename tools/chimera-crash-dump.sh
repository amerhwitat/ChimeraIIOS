#!/bin/sh
set -eu
STAMP=$(date -u +%Y%m%dT%H%M%SZ); ROOT=/var/crash/chimera/$STAMP
mkdir -p "$ROOT" /var/log/mesgs/archive
printf 'CHIMERA II OS CRASH DUMP\nUTC=%s\n' "$STAMP" > "$ROOT/README"
uname -a > "$ROOT/uname" 2>&1 || true
cat /proc/cmdline > "$ROOT/cmdline" 2>/dev/null || true
cat /proc/meminfo > "$ROOT/meminfo" 2>/dev/null || true
cat /proc/interrupts > "$ROOT/interrupts" 2>/dev/null || true
cat /proc/uptime > "$ROOT/uptime" 2>/dev/null || true
ps -eo pid,ppid,psr,stat,%cpu,%mem,etime,cmd --sort=-%cpu > "$ROOT/processes" 2>&1 || true
dmesg > "$ROOT/dmesg" 2>&1 || true
cp -a /var/log/mesgs "$ROOT/mesgs" 2>/dev/null || true
tar -czf "$ROOT/logs.tar.gz" /var/log/mesgs 2>/dev/null || true
printf '%s\n' "$ROOT"
