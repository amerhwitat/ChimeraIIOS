# Aurora Wayland Glass — World Language Support

Aurora uses Unicode, CLDR and BCP-47 as the foundation for world-language support. It does not maintain a hand-written finite list of “all languages”; the build can refresh the language/locale inventory from CLDR so new and updated locale data can be adopted without redesigning the desktop.

## Capabilities

- LTR and RTL desktop layouts.
- Mixed-direction text in the same window.
- Unicode Bidirectional Algorithm boundary.
- Language + script + region locale resolution.
- Script-aware font fallback and shaping.
- Arabic, Hebrew, Syriac, Persian/Urdu, Thaana, N'Ko and other RTL scripts through the same BiDi architecture.
- IME and composition support.
- Wayland text-input/input-method integration.
- Multilingual keyboard switching without restarting applications.
- Clipboard, selection, cursor, URL/path and numeric isolation for mixed scripts.
- Localized dates, times, numbers, currencies, units, collation and plural rules through CLDR.
- Accessibility, terminal, settings, package manager, games and Retro Center localization hooks.
- Translation-provider boundary without forcing a particular online translation service.
- Speech recognition/text-to-speech provider boundary.
- Handwriting and braille input provider boundaries.

## Architecture

```text
BCP-47 language tag
        ↓
CLDR locale + script resolver
        ↓
Unicode character/script properties
        ↓
BiDi + shaping + font fallback
        ↓
Wayland text-input / input-method
        ↓
Aurora Glass UI
        ↓
Applications and system services
```

The detailed machine-readable policy is `world_language_support.json`. `update_cldr_languages.py` is an explicit build/update helper for refreshing CLDR-derived locale information.

## Important distinction

Unicode explicitly models **scripts**, not languages. A single script can serve many languages and a language can use multiple scripts. Aurora therefore represents language, script, locale and direction independently. This is necessary for cases such as Serbian Latin/Cyrillic and Japanese Han/Hiragana/Katakana combinations.

Wayland text-input protocols provide UTF-8 text composition and language/input-method state; Aurora's desktop layer is designed around those protocol boundaries.

Proprietary fonts, speech engines, translation services and commercial language data are not silently redistributed. Their adapters remain explicit and license-aware.
