#!/usr/bin/env python3
"""Inject the wallpaper overlay into a repo HTML desktop page (static patch)."""
import json
import os
import sys

html_path, payload_root, default_wp = sys.argv[1], sys.argv[2], sys.argv[3]

manifest = json.load(open(os.path.join(payload_root, "wallpapers", "index.json")))
html_dir = os.path.dirname(os.path.abspath(html_path))
rel_root = os.path.relpath(os.path.join(payload_root, "wallpapers"), html_dir)
if not rel_root.endswith("/"):
    rel_root += "/"

wps = [{"name": w["name"], "url": rel_root + os.path.basename(w.get("url") or w["file"])} for w in manifest]
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallpaper_overlay.js")).read()
js = tpl.replace("__WALLPAPERS__", json.dumps(wps)).replace("__DEFAULT__", rel_root + default_wp)

snippet = "<script>/* aurora wallpaper overlay (build-time) */\n" + js + "\n</script>\n"

src = open(html_path, encoding="utf-8").read()
if "<!-- aurora wallpaper overlay (build-time) -->" in src:
    raise SystemExit("already patched: " + html_path)
snippet = "<!-- aurora wallpaper overlay (build-time) -->" + snippet
if "</body>" in src:
    src = src.replace("</body>", snippet + "</body>", 1)
else:
    src += snippet
open(html_path, "w", encoding="utf-8").write(src)
print("patched", html_path, "with", len(wps), "wallpapers, prefix", rel_root)
