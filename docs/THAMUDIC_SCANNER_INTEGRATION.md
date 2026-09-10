# Thamudic / Ancient North Arabian Scanner Integration

Chimera II OS now tracks the Thamudic/North Arabian inscription scanner as a language-research workload alongside the emulator, neural simulation and visualization layers.

## Canonical implementation

The current baseline scanner is maintained in the public `amerhwitat/nlp` repository as `thamudic_scanner.py`. It is intentionally a research-grade segmentation/evidence pipeline rather than a claim of fully automatic translation.

## External research and demo targets

- User-supplied Bubble prototype: https://thamudicscan.bubbleapps.io/version-test
- User-supplied translator UI: https://thamudicscan-s3wz30.public.builtwithrocket.new/
- User-supplied artifact database UI: https://thamudic-scanner.softr.app/
- OCIANA Thamudic overview: https://ociana.osu.edu/scripts_thamudic
- Unicode Old North Arabian: https://www.unicode.org/charts/nameslist/n_10A80.html
- Unicode Core Specification: https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-10/

## Architecture

`Image -> normalization -> segmentation -> glyph candidates -> evidence record -> optional classifier -> scholarly verification -> transliteration/translation -> web/API`

The same record schema can be consumed by Aurora/Web UI, Nucleus research storage and future Chimera neural/graph workloads.

## Unicode and script model

Old North Arabian is encoded at U+10A80–U+10A9F. The Unicode standard documents 28 letters and three number characters. Directionality, mirroring and regional/script variation must remain explicit metadata rather than being silently normalized away.

OCIANA emphasizes that “Thamudic” is not one uniform alphabet: Thamudic A became Taymanitic, E became Hismaic, F is associated with Himaitic, while B/C/D remain less fully studied. Chimera therefore uses a family/variety model and keeps corpus provenance.

## Open-source engineering references

Architecture patterns were reviewed from CuReD, Coptic Scriptorium OCR, historical Arabic OCR benchmarks and experimental hieroglyphic OCR. These are references for reproducibility, data/model separation and human-in-the-loop review. Their code/data are not copied into Chimera without license review.

## Quality rules

- Preserve original image and source/license information.
- Keep segmentation confidence separate from recognition confidence.
- Store competing readings rather than forcing one result.
- Never present an OCR candidate as a scholarly translation without verification.
- Preserve corpus identifiers, location/date metadata and apparatus notes.
- Separate established readings, hypotheses and visualization labels.

## Roadmap

1. Add line and inscription-panel detection.
2. Build a legally reusable, human-reviewed glyph dataset.
3. Add CPU-safe glyph classification and confidence calibration.
4. Add KMeans/PCA variant exploration.
5. Add OCIANA-linked evidence records.
6. Add Arabic/English/Hebrew transliteration editor.
7. Connect the scanner to the Aurora/Web UI and historical-artifact database layer.
8. Add reproducible CER/confusion-matrix benchmarks.
