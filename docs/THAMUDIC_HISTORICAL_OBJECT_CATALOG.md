# Thamudic / Ancient Historical Object Catalog Integration

The canonical Python research implementation lives in `amerhwitat/nlp` and now includes:

- `thamudic_scanner.py` — image normalization, segmentation and evidence extraction.
- `ancient_script_registry.py` — Ancient North Arabian and related script metadata.
- `historical_periods.py` — broad period taxonomy from Paleolithic through modern.
- `ancient_objects_db.py` — SQLite object/evidence/annotation database.
- `object_sources.py` — source normalization, provenance and IIIF support.
- `softr_export.py` — stable Softr import shape (CSV/JSON), including image-page and rights metadata.
- `softr_api.py` — optional Softr Database REST client using `SOFTR_API_KEY`.
- `scripts/populate_softr_jordan.py` — reproducible population utility for the reviewed Jordan seed.
- `data/jordan_heritage_seed.json` — reviewed seed records for important Jordanian sites, objects and artifacts.
- `thamudic_scanner_gui.py` — Tkinter main window for scanning, cataloging and export.

## Data flow

`Image/PDF/Web evidence -> normalization -> glyph candidates -> human review -> object metadata -> SQLite -> Softr CSV/JSON or Softr REST API -> Web UI`

## Jordan coverage

The first population set covers Ain Ghazal, Amman Citadel, Petra and Al-Khazneh, Dhiban/Dibon, Gadara/Umm Qais, Madaba Map, Quseir Amra, Umm er-Rasas, Jerash and Umm Al-Jimal. The Department of Antiquities of Jordan also identifies OCIANA, Manar al-Athar, Nabataean Studies, departmental publications, Islamic inscriptions and Qasr al-Mushatta as research databases/resources.

UNESCO currently lists eight Jordan World Heritage properties, including Petra, Quseir Amra, Um er-Rasas, As-Salt, the Baptism Site, Umm Al-Jimal and Wadi Rum; the catalog should continue expanding from these authoritative site records while adding museum/object-level evidence separately.

## Historical periods

The catalog intentionally supports broad period labels: Paleolithic, Epipaleolithic, Neolithic, Chalcolithic, Bronze Age, Iron Age, Hellenistic/Greek, Roman, Byzantine/Eastern Roman, Early Islamic, Medieval, Early Modern and Modern.

These are discovery labels, not substitutes for site-specific archaeological dating.

## Images and objects

The catalog stores source image URLs, image-page URLs, IIIF identifiers, local image paths, source record IDs, credits and rights statements. It does **not** assume that an image is reusable merely because an API exposes it. Each image retains the originating institution's rights metadata.

Wikimedia Commons images are referenced at item level and retain the creator/license information. Museum, UNESCO and institutional media are only added for redistribution when the specific item permits it.

## External sources researched

- OCIANA — Ancient North Arabian inscriptions, transliterations, translations, provenance, photographs/facsimiles.
- Department of Antiquities of Jordan — research databases including OCIANA, Manar al-Athar, Nabataean Studies, departmental publications, Islamic inscriptions and Qasr al-Mushatta.
- DASI — pre-Islamic Arabian inscriptions and anepigraphic objects.
- The Metropolitan Museum of Art Open Access — public-domain image/data resources where marked.
- Smithsonian Open Access — open metadata/media subject to item-level availability and rights.
- Europeana — cultural-heritage metadata/media and IIIF services with item-level rights.
- Wikimedia Commons / Wikidata — open-media and structured-data references with item-level licenses.
- UNESCO World Heritage Centre — authoritative site descriptions, conservation documents and item-specific media rights.
- IIIF — interoperable image delivery and region/size requests.

## Softr integration

Softr supports CSV import and a REST Database API. The Python project therefore exports a stable CSV/JSON schema and includes an optional API client. A live update requires the user's Softr API key plus database/table identifiers; no credential is stored in GitHub.

The Jordan seed can be reviewed with:

```bash
python scripts/populate_softr_jordan.py --database-id DB_ID --table-id TABLE_ID --dry-run
```

After authentication and schema verification, records can be inserted with the same command without `--dry-run`.

## Research quality rules

1. Never equate segmentation with recognition.
2. Never equate OCR candidate output with a scholarly translation.
3. Preserve competing readings and reviewer attribution.
4. Preserve image provenance, source URL, credit and rights statement.
5. Keep script identification separate from language identification.
6. Treat “Thamudic” as a historical umbrella/pending classification where appropriate; use Taymanitic, Hismaic, Himaitic, Safaitic, Dadanitic and other specific labels when supported.
7. Keep archaeological dates and object periods explicit and revisable.
8. Never copy an image into the repository merely because it is discoverable on the web; verify license/rights first.
9. Keep source evidence, interpretation and generated descriptions in separate fields.
10. Preserve a machine-readable audit trail for every imported record.
