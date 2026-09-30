# Aurora RTL/LTR text architecture

Aurora stores text logically as Unicode code points encoded as UTF-8. It never requires applications to store Arabic or Hebrew in visual order.

Every text container has a direction mode: auto, LTR, RTL or inherit. Auto uses Unicode bidirectional properties with first-strong paragraph detection. Explicit direction remains available for UI controls, filenames, terminals and mixed-language documents.

Rendering pipeline:
UTF-8 -> normalization -> grapheme segmentation -> BiDi resolution -> script shaping -> font fallback -> OpenType glyph positioning -> line breaking -> rasterization.

Arabic-family scripts require joining and shaping; Hebrew requires BiDi-aware ordering; mixed Arabic/Latin text requires embedding and isolation controls; numbers remain logically ordered and can be isolated when needed.

Legacy DOS/Windows text encodings are converted at compatibility boundaries and are not used as Aurora's internal representation.
