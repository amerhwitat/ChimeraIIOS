# Aurora multilingual and media architecture

## Unicode and UTF-8

Koronos now owns a freestanding UTF-8 scalar decoder/encoder for kernel input, IPC, filenames and desktop text boundaries. It rejects invalid, overlong, surrogate and out-of-range scalar values.

Aurora remains responsible for higher-level Unicode behavior: normalization, grapheme segmentation, bidirectional layout, script shaping, font fallback, emoji/variation handling and locale formatting.

## Languages

Aurora accepts BCP-47 language tags without a fixed language-count ceiling. Language packs, fonts, input methods, translation data and speech providers are discovered at runtime.

Arabic, Hebrew, Persian and Urdu require bidirectional layout and script shaping. CJK and Indic scripts require appropriate font/shaping data. Emoji requires suitable Unicode fonts. Full speech/translation coverage depends on installed and licensed language resources.

## Media

Media engines are upstream-owned projects. Chimera should build from pinned source revisions, retain notices and dependency/license manifests, and record SHA-256 hashes for generated binaries. This makes the media layer reproducible without redistributing proprietary components.

Desktop media MIME handlers resolve through the Aurora media service and then to the user's selected installed player.
