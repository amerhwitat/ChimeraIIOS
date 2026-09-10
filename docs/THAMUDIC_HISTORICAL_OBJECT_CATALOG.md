# Thamudic / Ancient Historical Object Catalog Integration

The canonical Python research implementation lives in `amerhwitat/nlp` and now includes:

- `thamudic_scanner.py` — image normalization, segmentation and evidence extraction.
- `ancient_script_registry.py` — Ancient North Arabian and related script metadata.
- `historical_periods.py` — broad period taxonomy from Paleolithic through modern.
- `ancient_objects_db.py` — SQLite object/evidence/annotation database.
- `object_sources.py` — source normalization, provenance and IIIF support.
- `softr_export.py` — stable Softr import shape (CSV/JSON).
- `softr_api.py` — optional Softr Database REST client using `SOFTR_API_KEY`.
- `thamudic_scanner_gui.py` — Tkinter main window for scanning, cataloging and export.

## Data flow

`Image/PDF -> normalization -> glyph candidates -> human review -> object metadata -> SQLite -> Softr CSV/JSON or Softr REST API -> Web UI`

## Historical periods

The catalog intentionally supports broad period labels: Paleolithic, Epipaleolithic, Neolithic, Chalcolithic, Bronze Age, Iron Age, Hellenistic/Greek, Roman, Byzantine/Eastern Roman, Early Islamic, Medieval, Early Modern and Modern.

These are discovery labels, not substitutes for site-specific archaeological dating.

## Images and objects

The catalog stores source image URLs, IIIF identifiers, local image paths, source record IDs, credits and rights statements. It does **not** assume that an image is reusable merely because an API exposes it. Each image retains the originating institution's rights metadata.

## External sources researched

- OCIANA — Ancient North Arabian inscriptions, transliterations, translations, provenance, photographs/facsimiles.
- DASI — pre-Islamic Arabian inscriptions and anepigraphic objects.
- The Metropolitan Museum of Art Open Access — public-domain image/data resources where marked.
- Smithsonian Open Access — open metadata/media subject to item-level availability and rights.
- Europeana — cultural-heritage metadata/media and IIIF services with item-level rights.
- IIIF — interoperable image delivery and region/size requests.

## Softr integration

Softr supports CSV import and a REST Database API. The Python project therefore exports a stable CSV/JSON schema and includes an optional API client. A live update requires the user's Softr API key plus database/table identifiers; no credential is stored in GitHub.

## Research quality rules

1. Never equate segmentation with recognition.
2. Never equate OCR candidate output with a scholarly translation.
3. Preserve competing readings and reviewer attribution.
4. Preserve image provenance, source URL, credit and rights statement.
5. Keep script identification separate from language identification.
6. Treat “Thamudic” as a historical umbrella/pending classification where appropriate; use Taymanitic, Hismaic, Himaitic, Safaitic, Dadanitic and other specific labels when supported.
7. Keep archaeological dates and object periods explicit and revisable.
