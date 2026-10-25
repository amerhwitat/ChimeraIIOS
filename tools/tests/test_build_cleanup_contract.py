#!/usr/bin/env python3
"""Guard generated-artifact cleanup and fail-closed Docker publication in the ISO builder."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "build-chimera-iso.sh"


def main() -> int:
    if not SCRIPT.is_file():
        print("BUILD CLEANUP FAIL: canonical ISO builder missing", file=sys.stderr)
        return 1
    text = SCRIPT.read_text(encoding="utf-8")
    required = (
        'CHIMERA_PUSH="${CHIMERA_PUSH:-0}"',
        "CHIMERA_BUILD_ID",
        "--label chimera.rootfs.export=true",
        "chimera.rootfs.owner=$CHIMERA_BUILD_ID",
        "chimera.rootfs.owner=$owner",
        'docker create --label chimera.rootfs.export=true --label "chimera.rootfs.owner=$CHIMERA_BUILD_ID" --name "$cname"',
        'find "$ROOTFS_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +',
        '[[ -n "$daps_verifier" && -f "$daps_verifier" ]]',
        '[[ -n "$daps_evidence" && -f "$daps_evidence" ]]',
        'python3 "$daps_verifier" --evidence "$daps_evidence"',
        "docker image rm \"$image\"",
        "report docker-publish",
    )
    for token in required:
        if token not in text:
            print(f"BUILD CLEANUP FAIL: missing safety contract: {token}", file=sys.stderr)
            return 1
    if "--filter 'label=chimera.rootfs.export=true'" in text:
        print("BUILD CLEANUP FAIL: global exporter-container deletion is forbidden", file=sys.stderr)
        return 1
    if "docker container prune -f" in text:
        print("BUILD CLEANUP FAIL: global container prune is forbidden", file=sys.stderr)
        return 1
    if "docker image rm -f \"$tagged\"" in text:
        print("BUILD CLEANUP FAIL: cleanup removes all tags sharing an image ID", file=sys.stderr)
        return 1
    print("BUILD CLEANUP PASS: scoped cleanup, safe rootfs clearing, and DAPS-gated image publication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
