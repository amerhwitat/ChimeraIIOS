"""Small dependency-free localization/RTL contract for Chimera desktops."""
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class Locale:
    id: str
    language: str
    direction: str
    script: str

ARABIC_SA = Locale("ar-SA", "ar", "rtl", "Arabic")
ENGLISH_US = Locale("en-US", "en", "ltr", "Latin")

def locale_for(value: str | None) -> Locale:
    value = (value or "en-US").replace("_", "-").lower()
    return ARABIC_SA if value.startswith("ar") else Locale(value, value.split("-", 1)[0], "rtl" if value.startswith("he") else "ltr", "Hebrew" if value.startswith("he") else "Latin")

def load_catalog(root: Path, locale: Locale = ARABIC_SA) -> dict:
    path = root / "desktop" / "localization" / f"{locale.language}-SA.json"
    return json.loads(path.read_text(encoding="utf-8"))
