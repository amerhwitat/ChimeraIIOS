#!/usr/bin/env bash
set -euo pipefail

# Reproducibly fetch upstream source trees into an ignored staging directory.
# This script intentionally does not rewrite upstream code or merge licenses.

ROOT="${CHIMERA_UPSTREAM_DIR:-third_party/upstream}"
mkdir -p "$ROOT"

clone_or_update() {
  local name="$1" url="$2"
  if [[ -d "$ROOT/$name/.git" ]]; then
    git -C "$ROOT/$name" fetch --tags --prune
    git -C "$ROOT/$name" pull --ff-only
  else
    git clone --filter=blob:none "$url" "$ROOT/$name"
  fi
}

clone_or_update coreutils https://git.savannah.gnu.org/git/coreutils.git
clone_or_update util-linux https://github.com/util-linux/util-linux.git
clone_or_update iproute2 https://git.kernel.org/pub/scm/network/iproute2/iproute2.git
clone_or_update sudo https://github.com/sudo-project/sudo.git
clone_or_update toybox https://github.com/landley/toybox.git
clone_or_update linux https://github.com/torvalds/linux.git

printf '\nUpstream trees are staged under %s. Review each project license/SPDX metadata before vendoring source into a distributable Chimera image.\n' "$ROOT"
