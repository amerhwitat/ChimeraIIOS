# Thamudic NLP / Epigraphy Laboratory

This integration reproduces the observable research workflow requested from the Thamudic Scanner experience inside Aurora Control Center.

## Features
- UTF-8 Ancient North Arabian / Thamudic Unicode U+10A80–U+10A9F.
- Image upload and connected-component segmentation.
- Deskew/read-order controls: auto, LTR, RTL, vertical, reversed, spiral, boustrophedon.
- Click-to-label glyphs.
- Transliteration and researcher translation fields.
- Local research search via Wikimedia Commons API.
- Provenance/source records and crawl metadata.
- Reviewed dataset manifest.
- Local model job/evaluation/prediction bridge.
- Lexicon editing.
- CSV, JSON-LD and TEI export.
- Explicit no-OCR/no-Tesseract policy.

## Source/crawl note
The supplied Softr URL did not expose a crawlable JavaScript/source bundle through the available retrieval channel, and no public GitHub repository matching the app/source was found. This repository therefore does not copy or claim proprietary source. The Web UI implements the observable research capabilities plus a TypeScript/Next.js adapter contract.

## Local bridge
Run:
```bash
python3 tools/thamudic-nlp/bridge.py
```

The browser UI remains static and GitHub-Pages-safe. Internet retrieval, image downloading, training and native ML remain local operations.
