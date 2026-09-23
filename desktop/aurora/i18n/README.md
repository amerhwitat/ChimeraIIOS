# Aurora Internationalization

Aurora uses a Unicode-first locale model. Applications must not assume left-to-right layout: UI geometry uses logical start/end, text uses Unicode bidirectional processing, and locale data should come from CLDR/ICU-compatible resources.

The target is broad Unicode language coverage rather than claiming that every language has a completed human translation. A language can therefore be represented by locale, script, keyboard/input method and fallback resources even before a full translation pack exists.

RTL locales mirror eligible controls and menus; content whose semantic direction must remain stable (graphs, clocks, media timelines and directional imagery) remains stable. Mixed Arabic/Hebrew plus Latin/numeric text uses bidi-aware layout.

Input sources can be switched independently from display language, following the Windows/macOS model. Windows supports installing display languages and alternate keyboard layouts, while macOS supports multiple input sources and bidi options. See Microsoft and Apple documentation in the repository's internationalization notes.
