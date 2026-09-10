# Chimera II OS Thamudic subsystem

The North Arabian/Thamudic scanner is exposed as a language-neutral service contract. Native implementations live in `amerhwitat/nlp`: C++20, Java 21, Node.js ESM, Visual C++/MSVC and C#/.NET 8/9/10.

Koronos/Aurora integrations should consume normalized Unicode glyph records, bounding boxes, transliteration maps and JSON interchange envelopes rather than duplicate OCR logic.

Supported script families remain independently classified: Thamudic/Ancient North Arabian, Safaitic, Hismaic, Dadanitic and Early Arabic. The subsystem does not assume they share one glyph inventory.
