#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/usr/share/chimera"
INSTALLER="$ROOT/installer/chimera_installer.py"
PLAN_DIR="${XDG_RUNTIME_DIR:-/run}/chimera-installer"
PLAN="$PLAN_DIR/install-plan.json"
mkdir -p "$PLAN_DIR"

command -v python3 >/dev/null 2>&1 || {
  echo "[Aurora Installer] Python 3 is required."
  exit 1
}

choose_edition() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --list --radiolist       --title="Chimera II OS Installer — Aurora"       --text="Choose the Chimera II OS edition"       --column="Select" --column="Edition" --column="Purpose"       TRUE desktop "Aurora Wayland Glass workstation"       FALSE server "Routing, services, storage and compute"       FALSE mobile "Mobile hardware profile"       FALSE edge "Edge / network / AI node"       FALSE iot "Constrained embedded / IoT"       FALSE cvel "Virtualized / experimental edition"       --height=420 --width=780
    return
  fi
  printf '%s\n' desktop
}

show_plan() {
  local edition="$1"
  python3 "$INSTALLER" --edition "$edition" --output "$PLAN" >"$PLAN_DIR/inventory.json"
  if command -v zenity >/dev/null 2>&1; then
    zenity --text-info --title="Chimera II OS Installation Plan"       --filename="$PLAN" --width=1000 --height=700
  else
    cat "$PLAN"
  fi
}

confirm_apply() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --question       --title="Chimera II OS — Explicit Installation Confirmation"       --width=720       --text="The current installer contract requires explicit confirmation before destructive disk operations.\n\nThe current repository installer generates and reviews the installation plan; platform-specific disk/boot mutation remains a signed backend operation.\n\nContinue to create the reviewed plan?"
  else
    read -r -p "Create reviewed installation plan? [y/N] " answer
    [[ "$answer" =~ ^[Yy]$ ]]
  fi
}

edition="$(choose_edition)" || exit 0
[[ -n "$edition" ]] || exit 0

show_plan "$edition" || {
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --text="Unable to generate the Chimera installation plan."
  fi
  exit 1
}

if confirm_apply; then
  if command -v zenity >/dev/null 2>&1; then
    zenity --info --title="Chimera II OS Installer"       --text="Installation plan saved to:\n$PLAN\n\nNo disk is erased by this step. The reviewed plan is ready for the signed platform installer backend."
  else
    printf '\nPlan saved: %s\nNo disk was modified.\n' "$PLAN"
  fi
fi
