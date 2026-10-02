#!/usr/bin/env bash
set -euo pipefail

# Probe connected mobile devices without modifying them.
# Reports USB/ADB/Fastboot identity and available hardware properties.

have(){ command -v "$1" >/dev/null 2>&1; }
json_escape(){ printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

printf '{\n  "timestamp": "%s",\n  "devices": [\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
first=1
emit(){
  local transport="$1" id="$2" maker="$3" model="$4" arch="$5" state="$6" unlock="$7" props="$8"
  (( first )) || printf ',\n'; first=0
  printf '    {"transport":"%s","id":"%s","manufacturer":"%s","model":"%s","architecture":"%s","state":"%s","unlock_state":"%s","properties":%s}' \
    "$(json_escape "$transport")" "$(json_escape "$id")" "$(json_escape "$maker")" "$(json_escape "$model")" "$(json_escape "$arch")" "$(json_escape "$state")" "$(json_escape "$unlock")" "$props"
}

if have adb; then
  adb start-server >/dev/null 2>&1 || true
  while IFS=$'\t' read -r serial state; do
    [[ -z "${serial:-}" ]] && continue
    [[ "$serial" == "List of devices attached" ]] && continue
    maker=$(adb -s "$serial" shell getprop ro.product.manufacturer 2>/dev/null | tr -d '\r' || true)
    model=$(adb -s "$serial" shell getprop ro.product.model 2>/dev/null | tr -d '\r' || true)
    arch=$(adb -s "$serial" shell getprop ro.product.cpu.abilist 2>/dev/null | tr -d '\r' || true)
    unlock=$(adb -s "$serial" shell getprop ro.boot.flash.locked 2>/dev/null | tr -d '\r' || true)
    [[ "$unlock" == "0" ]] && unlock=unlocked || [[ "$unlock" == "1" ]] && unlock=locked || unlock=unknown
    props=$(printf '{"soc":"%s","board":"%s","bootloader":"%s","android":"%s","abi":"%s"}' \
      "$(json_escape "$(adb -s "$serial" shell getprop ro.soc.model 2>/dev/null | tr -d '\r')")" \
      "$(json_escape "$(adb -s "$serial" shell getprop ro.product.board 2>/dev/null | tr -d '\r')")" \
      "$(json_escape "$(adb -s "$serial" shell getprop ro.bootloader 2>/dev/null | tr -d '\r')")" \
      "$(json_escape "$(adb -s "$serial" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')")" \
      "$(json_escape "$arch")")"
    emit adb "$serial" "$maker" "$model" "$arch" "$state" "$unlock" "$props"
  done < <(adb devices 2>/dev/null | tail -n +2)
fi

if have fastboot; then
  while read -r serial; do
    [[ -z "$serial" ]] && continue
    maker=$(fastboot -s "$serial" getvar product 2>&1 | sed -n 's/.*product:[[:space:]]*//p' | head -1)
    boot=$(fastboot -s "$serial" getvar unlocked 2>&1 | sed -n 's/.*unlocked:[[:space:]]*//p' | head -1)
    [[ -z "$boot" ]] && boot=unknown
    props=$(printf '{"product":"%s"}' "$(json_escape "$maker")")
    emit fastboot "$serial" "" "$maker" "unknown" "bootloader" "$boot" "$props"
  done < <(fastboot devices 2>/dev/null | awk '{print $1}')
fi

printf '\n  ]\n}\n'
