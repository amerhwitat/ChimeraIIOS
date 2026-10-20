#!/usr/bin/env python3
"""Stage Aurora artwork, media, menu catalogs, and icon themes into boot/runtime trees."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".wav", ".ogg", ".ttf", ".otf"}
CATALOGS = {"gates_menu.json", "menu-event-map.json", "icon_theme.json", "chimera-artwork-manifest.json",
            "library-artwork-manifest.json", "manifest.json", "language_catalog.json",
            "arabic_command_catalog.json", "context_menu.json"}

def collect():
    selected = set()
    for rel in ("desktop/aurora/assets", "desktop/aurora/icons", "desktop/aurora/input", "desktop/file_associations"):
        base = ROOT / rel
        if base.is_dir():
            for p in base.rglob("*"):
                if p.is_file() and (p.suffix.lower() in MEDIA or
                    (p.suffix.lower() == ".json" and (p.name in CATALOGS or any(k in p.name for k in ("menu", "icon", "context"))))):
                    selected.add(p)
    required = ("desktop/aurora/assets/Init.mp4", "desktop/aurora/assets/aurora-desktop.svg",
                "desktop/aurora/assets/aurora-installer.svg", "desktop/aurora/assets/aurora-library.svg",
                "desktop/aurora/icons/icon_theme.json", "desktop/aurora/gates_menu.json")
    missing = [x for x in required if not (ROOT / x).is_file() or (ROOT / x).stat().st_size == 0]
    if missing:
        raise RuntimeError("required desktop artifacts missing: " + ", ".join(missing))
    return sorted(selected)

def stage(destination: Path, sources: list[Path]):
    rows = []
    for source in sources:
        rel = source.relative_to(ROOT)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rows.append({"path": str(rel), "size": target.stat().st_size,
                     "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    destination.mkdir(parents=True, exist_ok=True)
    report = {"schema":"CHIMERA-DESKTOP-STAGE-1", "status":"staged-not-boot-verified",
              "file_count":len(rows), "files":rows}
    (destination / "desktop-artifact-inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rootfs", type=Path, default=ROOT / "build/rootfs")
    parser.add_argument("--iso-root", type=Path, required=True)
    args = parser.parse_args()
    sources = collect()
    report = stage(args.rootfs / "usr/share/chimera/desktop-assets", sources)
    stage(args.iso_root / "boot/visual/desktop-assets", sources)
    media = args.rootfs / "usr/share/chimera/aurora/assets"
    media.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "desktop/aurora/assets/Init.mp4", media / "Init.mp4")
    print(f"[DESKTOP-ASSETS] staged {report['file_count']} files; status=staged-not-boot-verified")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"[DESKTOP-ASSETS][ERROR] {exc}")
