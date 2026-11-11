#!/usr/bin/env bash
# Select an installed desktop session at login. Only launch sessions detected on
# this system; never advertise a profile whose executable is missing.
set -euo pipefail

chimera_desktop_sessions() {
  local rows=()
  rows+=("aurora" "Aurora Wayland Glass (default)")
  command -v marine-session >/dev/null 2>&1 && rows+=("marine" "Marine Desktop")
  command -v gnome-session >/dev/null 2>&1 && rows+=("gnome" "GNOME (installed)")
  command -v startplasma-wayland >/dev/null 2>&1 && rows+=("plasma" "KDE Plasma Wayland (installed)")
  command -v startxfce4 >/dev/null 2>&1 && rows+=("xfce" "Xfce (installed)")
  command -v cinnamon-session >/dev/null 2>&1 && rows+=("cinnamon" "Cinnamon (installed)")
  printf '%s\n' "${rows[@]}"
}

chimera_select_desktop_profile() {
  local config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/chimera"
  local selected="" saved=""
  mkdir -p "$config_dir"
  saved="$(cat "$config_dir/desktop-session" 2>/dev/null || true)"
  local -a rows=()
  mapfile -t rows < <(chimera_desktop_sessions)
  local -a choices=()
  local i
  for ((i=0; i<${#rows[@]}; i+=2)); do
    choices+=("${rows[i]}" "${rows[i+1]}")
  done

  if [[ "${CHIMERA_DESKTOP_SELECT:-auto}" == "never" ]]; then
    selected="$saved"
  elif command -v zenity >/dev/null 2>&1 && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    selected="$(zenity --list --title="Choose desktop" --text="Select the desktop session for this login" --column="Session" --column="Description" --hide-column=1 --print-column=1 --height=360 --width=520 "${choices[@]}" 2>/dev/null || true)"
  elif command -v whiptail >/dev/null 2>&1 && [[ -t 0 ]]; then
    selected="$(whiptail --title "Choose desktop" --menu "Select the desktop session for this login" 18 72 8 "${choices[@]}" 3>&1 1>&2 2>&3 || true)"
  elif [[ -t 0 && "${CHIMERA_DESKTOP_SELECT:-auto}" != "never" ]]; then
    printf '\nAvailable desktop sessions:\n' >&2
    for ((i=0; i<${#rows[@]}; i+=2)); do printf '  %s) %s\n' "${rows[i]}" "${rows[i+1]}" >&2; done
    read -r -p "Desktop [${saved:-aurora}]: " selected || true
  else
    selected="$saved"
  fi

  [[ -n "$selected" ]] || selected="$saved"
  case "$selected" in
    aurora) CHIMERA_SELECTED_DESKTOP=aurora ;;
    marine) command -v marine-session >/dev/null 2>&1 || selected=aurora; CHIMERA_SELECTED_DESKTOP="$selected" ;;
    gnome) command -v gnome-session >/dev/null 2>&1 || selected=aurora; CHIMERA_SELECTED_DESKTOP="$selected" ;;
    plasma) command -v startplasma-wayland >/dev/null 2>&1 || selected=aurora; CHIMERA_SELECTED_DESKTOP="$selected" ;;
    xfce) command -v startxfce4 >/dev/null 2>&1 || selected=aurora; CHIMERA_SELECTED_DESKTOP="$selected" ;;
    cinnamon) command -v cinnamon-session >/dev/null 2>&1 || selected=aurora; CHIMERA_SELECTED_DESKTOP="$selected" ;;
    *) CHIMERA_SELECTED_DESKTOP=aurora ;;
  esac
  printf '%s\n' "$CHIMERA_SELECTED_DESKTOP" > "$config_dir/desktop-session"
  export CHIMERA_SELECTED_DESKTOP
}
