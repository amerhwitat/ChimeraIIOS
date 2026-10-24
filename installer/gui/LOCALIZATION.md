# Installer localization contract

The graphical installer accepts BCP-47 locale tags and UTF-8 text independently for:
- installer display language;
- installed system locale;
- console keyboard layout;
- comma-separated input-language tags;
- IANA timezone.

The bundled catalog currently contains translated core wizard labels and safety messaging for English, Arabic, Spanish, French, German, Portuguese, Russian, Chinese, Japanese, Hindi, Urdu, and Turkish. The picker also lists additional language names and accepts a valid browser locale. When a language has no bundled translation, the UI explicitly falls back to English instead of pretending a translation exists.

Arabic, Persian, Hebrew, Urdu, Pashto, Divehi, Syriac, N'Ko, Uyghur, Yiddish, and Central Kurdish locales are assigned right-to-left document direction. Unicode is preserved; the locale picker does not alter the system locale or input-language settings without a separate explicit choice.

The browser preview remains review-only. Localization does not enable disk writes or bypass the native installer transaction gate. The ISO must package `installer-i18n.js` alongside the HTML and main wizard script; the release workflow hashes all three assets.
