# Thamudic / Ancient North Arabian Scanner Integration

Chimera II OS tracks the Thamudic/North Arabian inscription scanner as a language-research workload alongside emulation, neural simulation and visualization.

## Canonical Python implementation

The baseline scanner is maintained in the public `amerhwitat/nlp` repository:

- `thamudic_scanner.py` — image normalization, segmentation, connected components and evidence records.
- `ancient_script_registry.py` — script/variety metadata and Unicode ranges.
- `thamudic_scanner_gui.py` — **Tkinter main window** for importing images, scanning, human review and exporting records.
- `tests/test_thamudic_scanner.py` — deterministic scanner tests.

The GUI is the primary desktop import/export interface. It intentionally separates segmentation, recognition candidates, transliteration and translation so that a visual candidate is never silently promoted to a scholarly reading.

## Supported research registry

The registry currently covers Old North Arabian plus Thamudic B/C/D, Taymanitic, Hismaic, Himaitic, Safaitic, Dadanitic, Dumaitic and Hasaitic, plus Ancient South Arabian Sabaic/Minaic/Qatabanic/Hadramitic and related Phoenician, Aramaic and Nabataean script families. Script-family labels remain evidence metadata; the scanner does not infer a definitive language solely from a glyph image.

## External research and demo targets

- User-supplied Bubble prototype: https://thamudicscan.bubbleapps.io/version-test
- User-supplied translator UI: https://thamudicscan-s3wz30.public.builtwithrocket.new/
- User-supplied artifact database UI: https://thamudic-scanner.softr.app/
- OCIANA: https://ociana.osu.edu/
- OCIANA Thamudic overview: https://ociana.osu.edu/scripts_thamudic
- Unicode Old North Arabian: https://www.unicode.org/charts/nameslist/n_10A80.html
- Unicode Core Specification: https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-10/

These external applications and datasets are reference targets. Their code/data are not copied into Chimera without explicit permission and license review.

## Architecture

`Image -> normalization -> segmentation -> glyph candidates -> evidence record -> optional classifier -> human/scholarly verification -> transliteration -> translation/interpretation -> JSON/CSV/TXT -> Aurora/Web/API`

The same evidence record can be consumed by Aurora/Web UI, Nucleus research storage and future Chimera neural/graph workloads.

## Scholarly model

OCIANA emphasizes that “Thamudic” is not one uniform alphabet: former Thamudic A is Taymanitic, E is Hismaic and F is associated with Himaitic, while B/C/D remain less fully studied. The software therefore uses a family/variety model and preserves corpus provenance rather than forcing one universal Thamudic alphabet.

## Research findings incorporated

Recent research includes deep-learning work on predicting Thamudic inscription sequence/context and broader surveys of ancient-script image recognition. Open-source engineering references include Coptic Scriptorium OCR, CuReD, historical Arabic OCR work and experimental hieroglyphic OCR. These are architectural references only; third-party code and datasets require independent license/provenance review.

## Quality rules

- Preserve original image and source/license information.
- Keep segmentation confidence separate from recognition confidence.
- Store competing readings rather than forcing one result.
- Never present an OCR candidate as a scholarly translation without verification.
- Preserve corpus identifiers, location/date metadata and apparatus notes.
- Separate established readings, hypotheses and visualization labels.
- Keep script identification distinct from language identification.

## Roadmap

1. Add line and inscription-panel detection.
2. Build a legally reusable, human-reviewed glyph dataset.
3. Add CPU-safe glyph classification and confidence calibration.
4. Add KMeans/PCA variant exploration.
5. Add OCIANA-linked evidence records.
6. Add Arabic/English/Hebrew transliteration editor.
7. Connect the scanner to the Aurora/Web UI and historical-artifact database layer.
8. Add reproducible CER/confusion-matrix benchmarks.
9. Add pluggable ancient-script recognition models without changing the evidence schema.
10. Add batch PDF/document ingestion through `PDFreaderPY` while retaining source-page provenance.
