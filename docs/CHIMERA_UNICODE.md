# Chimera II Unicode contract

Aurora uses UTF-8 end-to-end for desktop text, CLI output, shell input, terminal profiles and native utilities.

The native layer provides UTF-8 validation and decoding, Unicode scalar encoding, malformed-input sanitization, combining-mark and variation-selector recognition, RTL code-point detection, conservative display-width calculation, emoji detection and stable :name: aliases. Aurora also contains a small original hardcoded SVG icon fallback for core system actions.

Wayland text-input specifications define text as UTF-8 and cursor/selection indices as byte offsets, which matches this architecture. The text-input protocol also defines a terminal content purpose and an explicit no-emoji hint, allowing applications to control emoji presentation where appropriate. citeturn0search2turn0search4

Unicode CLDR supplies the broader locale and emoji annotation data family. The Chimera runtime keeps a dependency-light core catalog while permitting richer CLDR data to be packaged later. Unicode Emoji 18.0 defines the current emoji structure and sequences. citeturn0search16turn0search17
