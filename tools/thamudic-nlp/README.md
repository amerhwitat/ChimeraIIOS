# Thamudic NLP / Epigraphy Laboratory

Chimera II now includes a real local NLP backend for the Thamudic Scanner workflow. The Web UI remains GitHub-Pages-safe while the local bridge supplies NLP, corpus lookup, provenance and optional provider integration.

## NLP backend

Run: `python3 tools/thamudic-nlp/bridge.py`

The bridge listens on `127.0.0.1:8766` by default.

Endpoints:
- `GET /nlp/capabilities` — backend/provider/corpus capabilities.
- `GET /nlp/catalog` — registered reviewed corpus catalog.
- `POST /nlp/transliterate` — Unicode normalization, segmentation and glyph transliteration.
- `POST /nlp/translate` — evidence-aware translation using the local reviewed corpus or an external provider.
- `POST /nlp/analyze` — full token/provenance/uncertainty analysis.
- `GET /health` — reports the NLP backend instead of the previous “No NLP backend configured” state.

Example: `{"text":"𐪀𐪁𐪂","target":"english","mode":"research"}`

## Provider integration

Set `THAMUDIC_PROVIDER_URL` to a compatible JSON POST endpoint when a scholarly/provider corpus is available:

`THAMUDIC_PROVIDER_URL=http://127.0.0.1:9000/translate python3 tools/thamudic-nlp/bridge.py`

The bridge sends `text`, `target`, `mode` and `script=thamudic`. If the provider is unavailable, the bridge falls back to the local reviewed corpus and reports the provider error in provenance.

## Research safety

The local backend does not fabricate historical meanings. Glyphs that cannot be supported by the registered corpus remain uncertain, while transliteration can still proceed. Corpus entries are explicitly structured with source and confidence metadata so reviewed scholarship can be added without changing the UI contract.

## Existing scanner features

- UTF-8 Ancient North Arabian / Thamudic Unicode U+10A80–U+10A9F.
- Image upload and connected-component segmentation.
- Deskew/read-order controls.
- Click-to-label glyphs.
- Transliteration and researcher translation fields.
- Local research search via Wikimedia Commons API.
- Provenance/source records and crawl metadata.
- Reviewed dataset manifest.
- Local model job/evaluation/prediction bridge.
- Lexicon editing.
- CSV, JSON-LD and TEI export.

The supplied Softr URL did not expose a crawlable JavaScript/source bundle through the available retrieval channel, and no public GitHub repository matching the app/source was found. This implementation is original and does not claim proprietary source.