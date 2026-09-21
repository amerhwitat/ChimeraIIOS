#!/usr/bin/env python3
"""Aurora wallpaper metadata/cache manager. Downloads only from configured providers."""
import json,os,pathlib,time,urllib.request
CFG=pathlib.Path(os.environ.get("CHIMERA_WALLPAPER_CONFIG","/etc/chimera/aurora-wallpaper.json"))
STATE=pathlib.Path(os.environ.get("CHIMERA_WALLPAPER_STATE","/var/lib/chimera/aurora/wallpapers.json"))
def main():
    STATE.parent.mkdir(parents=True,exist_ok=True)
    data={"enabled":False,"providers":[],"last_update":0}
    if CFG.exists():
        try:data=json.loads(CFG.read_text())
        except Exception:pass
    # Provider adapters populate approved image URLs and attribution metadata.
    # This daemon deliberately does not scrape arbitrary sites.
    STATE.write_text(json.dumps({"timestamp":time.time(),"config":data},indent=2))
if __name__=="__main__": main()
