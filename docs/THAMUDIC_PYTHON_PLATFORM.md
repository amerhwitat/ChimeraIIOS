# Thamudic Python Platform Integration

Chimera II OS treats the Thamudic research stack as a Python-native research application that can be surfaced through Aurora/Web UI without requiring a TypeScript runtime.

## Components

- Python scanner: `thamudic_scanner.py`
- SQLite evidence database: `ancient_objects_db.py`
- Professional Tkinter/ttk desktop: `thamudic_desktop.py`
- Flask web application/API: `thamudic_web_app.py`
- Unified launcher: `run_thamudic.py`
- PDF ingestion: `PDFreaderPY`

## Architecture

```text
PDF / image
   -> PDFreaderPY / scanner
   -> evidence + glyph segmentation
   -> SQLite
   -> Python desktop or Flask web UI
   -> Aurora / Chimera II OS integration
```

The same record model is used across interfaces. JSON, CSV and SQL remain interoperability formats. Recognition and translation are explicitly evidence-aware and human-reviewable.

The Python-first design avoids coupling the research application to a Next.js/TypeScript runtime while keeping the web interface available through Flask.
