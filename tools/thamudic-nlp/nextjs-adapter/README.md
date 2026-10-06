# Next.js / TypeScript adapter contract

This is an original integration contract for Chimera II, not copied Softr source.

Use it from a Next.js App Router route or server action to proxy the local Thamudic bridge. Keep the bridge URL server-side and never expose private model files or credentials.

Suggested routes:
- /api/thamudic/search
- /api/thamudic/crawl
- /api/thamudic/train
- /api/thamudic/predict
- /api/thamudic/evaluate

The public GitHub Pages build continues to use the native browser UI in `web/`; this adapter exists for a future Next.js deployment without changing the research data contract.
