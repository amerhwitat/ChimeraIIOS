#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$ROOT/tools/mobile/chimera-mobile-flash.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/fastboot" <<'MOCK'
#!/usr/bin/env sh
: "${CHIMERA_FASTBOOT_MARKER:?}"
printf '%s\n' "$*" >> "$CHIMERA_FASTBOOT_MARKER"
exit 0
MOCK
chmod +x "$TMP/fastboot"

export CHIMERA_FASTBOOT_MARKER="$TMP/fastboot-writes"
if PATH="$TMP:$PATH" "$TOOL" generic-flash >"$TMP/output.log" 2>&1; then
  echo "FAIL: generic-flash unexpectedly succeeded" >&2
  exit 1
fi
grep -Fq 'generic-flash is disabled' "$TMP/output.log"
test ! -e "$CHIMERA_FASTBOOT_MARKER"
echo "PASS: generic-flash is rejected before any Fastboot invocation"
