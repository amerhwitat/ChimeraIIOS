#!/bin/sh
set -eu
CONFIG=${CHIMERA_DRIVER_REPOSITORIES:-/etc/chimera/drivers/driver-repositories.json}
DB=/var/lib/chimera/drivers
LOG=/var/log/mesgs
CACHE="$DB/repository-cache"
QUARANTINE="$DB/quarantine"
mkdir -p "$CACHE" "$DB/downloads" "$QUARANTINE" "$DB/build" "$DB/state" "$LOG"
log(){ printf '[DRIVER] %s\n' "$*" >> "$LOG/mesgs" 2>/dev/null || true; }
have(){ command -v "$1" >/dev/null 2>&1; }
fetch(){
  url="$1"; out="$2"
  if have curl; then curl -fL --retry 2 --connect-timeout 10 -A 'ChimeraIIOS-DriverManager/1.0' "$url" -o "$out"
  elif have wget; then wget -q --tries=2 --timeout=20 --user-agent='ChimeraIIOS-DriverManager/1.0' -O "$out" "$url"
  else return 127; fi
}
inventory(){
  : > "$DB/state/hardware.inventory"
  if [ -d /sys/bus/pci/devices ]; then
    for d in /sys/bus/pci/devices/*; do
      [ -d "$d" ] || continue
      printf 'pci %s %s %s\n' "$(basename "$d")" "$(cat "$d/vendor" 2>/dev/null || echo unknown)" "$(cat "$d/device" 2>/dev/null || echo unknown)" >> "$DB/state/hardware.inventory"
    done
  fi
  if [ -d /sys/bus/usb/devices ]; then
    for d in /sys/bus/usb/devices/*:*; do
      [ -d "$d" ] || continue
      printf 'usb %s %s %s\n' "$(basename "$d")" "$(cat "$d/idVendor" 2>/dev/null || echo unknown)" "$(cat "$d/idProduct" 2>/dev/null || echo unknown)" >> "$DB/state/hardware.inventory"
    done
  fi
  while IFS= read -r line; do log "$line"; done < "$DB/state/hardware.inventory"
}
search(){
  inventory
  log "Searching configured driver, firmware and hardware-ID sources."
  if have wget || have curl; then
    fetch 'https://pci-ids.ucw.cz/v2.2/pci.ids' "$CACHE/pci.ids" 2>/dev/null || fetch 'https://pci-ids.ucw.cz/pci.ids' "$CACHE/pci.ids" 2>/dev/null || true
    [ -s "$CACHE/pci.ids" ] && log "PCI ID database refreshed" || log "PCI ID database refresh unavailable"
  else
    log "No network downloader available; retaining offline cache."
  fi
  log "Repository registry: $CONFIG"
  log "Native candidates: Chimera-native packages, Chimera source builds, and firmware."
  log "Foreign driver formats are quarantined until a Chimera compatibility provider validates them."
}
install_candidate(){
  file="$1"
  [ -f "$file" ] || { log "Candidate not found: $file"; return 1; }
  case "$file" in
    *.chm-driver|*.chmfw|*.fw|*.bin)
      mkdir -p /lib/chimera/drivers /lib/firmware
      cp -f "$file" /lib/chimera/drivers/ 2>/dev/null || cp -f "$file" /lib/firmware/
      log "Installed native/firmware candidate: $file";;
    *.ko|*.sys|*.dll|*.kext|*.dext|*.inf)
      cp -f "$file" "$QUARANTINE/"
      log "Quarantined foreign driver: $file";;
    *) cp -f "$file" "$QUARANTINE/"; log "Unknown driver artifact quarantined: $file";;
  esac
}
case "${1:-search}" in
  inventory) inventory;;
  search|update) search;;
  install) install_candidate "${2:-}";;
  daemon) while :; do search || true; sleep "${CHIMERA_DRIVER_REFRESH_SECONDS:-21600}"; done;;
  *) echo 'usage: chimera-driver-manager {inventory|search|update|install FILE|daemon}'; exit 2;;
esac
