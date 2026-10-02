#!/usr/bin/env bash
set -euo pipefail

# Probe connected mobile devices without modifying them.
# Produces valid JSON for ADB and Fastboot targets.

have() { command -v "$1" >/dev/null 2>&1; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:-}
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

# TSV fields:
# transport, id, manufacturer, model, architecture, state, unlock_state,
# soc, board, bootloader, android, product
: > "$TMP"

if have adb; then
    adb start-server >/dev/null 2>&1 || true
    while IFS=$'\t' read -r serial state; do
        [[ -n "${serial:-}" ]] || continue

        maker=$(adb -s "$serial" shell getprop ro.product.manufacturer 2>/dev/null | tr -d '\r' || true)
        model=$(adb -s "$serial" shell getprop ro.product.model 2>/dev/null | tr -d '\r' || true)
        arch=$(adb -s "$serial" shell getprop ro.product.cpu.abilist 2>/dev/null | tr -d '\r' || true)
        unlock=$(adb -s "$serial" shell getprop ro.boot.flash.locked 2>/dev/null | tr -d '\r' || true)
        soc=$(adb -s "$serial" shell getprop ro.soc.model 2>/dev/null | tr -d '\r' || true)
        board=$(adb -s "$serial" shell getprop ro.product.board 2>/dev/null | tr -d '\r' || true)
        bootloader=$(adb -s "$serial" shell getprop ro.bootloader 2>/dev/null | tr -d '\r' || true)
        android=$(adb -s "$serial" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r' || true)

        case "$unlock" in
            0) unlock=unlocked ;;
            1) unlock=locked ;;
            *) unlock=unknown ;;
        esac

        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            adb "$serial" "$maker" "$model" "$arch" "$state" "$unlock" \
            "$soc" "$board" "$bootloader" "$android" "" >> "$TMP"
    done < <(adb devices 2>/dev/null | awk 'NR > 1 && NF {print $1 "\t" $2}')
fi

if have fastboot; then
    while IFS= read -r serial; do
        [[ -n "$serial" ]] || continue

        product=$(fastboot -s "$serial" getvar product 2>&1 \
            | sed -n 's/.*product:[[:space:]]*//p' | head -n 1 || true)
        unlocked=$(fastboot -s "$serial" getvar unlocked 2>&1 \
            | sed -n 's/.*unlocked:[[:space:]]*//p' | head -n 1 || true)
        [[ -n "$unlocked" ]] || unlocked=unknown

        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            fastboot "$serial" "" "$product" unknown bootloader "$unlocked" \
            "" "" "" "" "$product" >> "$TMP"
    done < <(fastboot devices 2>/dev/null | awk 'NF {print $1}')
fi

# Generate JSON with Python so shell quoting/escaping cannot corrupt the document.
python3 - "$TMP" "$OUT" <<'PY'
import json
import sys
from datetime import datetime, timezone

src, out = sys.argv[1], sys.argv[2]
devices = []

with open(src, encoding="utf-8") as fh:
    for line in fh:
        fields = line.rstrip("\n").split("\t")
        fields += [""] * (12 - len(fields))
        (
            transport, ident, maker, model, arch, state, unlock,
            soc, board, bootloader, android, product,
        ) = fields[:12]

        devices.append({
            "transport": transport,
            "id": ident,
            "manufacturer": maker,
            "model": model,
            "architecture": arch,
            "state": state,
            "unlock_state": unlock,
            "properties": {
                "soc": soc,
                "board": board,
                "bootloader": bootloader,
                "android": android,
                "product": product,
                "abi": arch,
            },
        })

payload = {
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "devices": devices,
}

text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
if out:
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
print(text, end="")
PY
