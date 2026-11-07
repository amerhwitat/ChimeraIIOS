#!/usr/bin/env python3
"""Contract tests for Aurora desktop audio feedback and its local assets."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SHELL=ROOT/"desktop/aurora-shell/assets/shell.js"
INDEX=ROOT/"desktop/aurora-shell/index.html"
SOUND_DIR=ROOT/"desktop/aurora/assets/sounds"
def main():
    source=SHELL.read_text(encoding="utf-8")
    page=INDEX.read_text(encoding="utf-8")
    manifest=json.loads((SOUND_DIR/"manifest.json").read_text(encoding="utf-8"))
    required={
      "startup":"startup.wav",
      "menu_open":"menu-open.wav",
      "menu_focus":"menu-focus.wav",
      "menu_select":"menu-select.wav",
      "menu_back":"menu-back.wav",
      "cancel":"cancel.wav",
      "warning":"warning.wav",
      "error":"error.wav",
      "success":"success.wav",
    }
    for event,filename in required.items():
        assert manifest["events"].get(event)==filename, f"manifest event mismatch: {event}"
        assert (SOUND_DIR/filename).is_file(), f"sound asset missing: {filename}"
        assert f'{event}: "{filename}"' in source, f"shell does not map sound event: {event}"
    assert "function playSound(eventName)" in source
    assert 'button.matches("#mbMenus button") ? "menu_open" : "menu_select"' in source
    assert 'target.matches("button,[role=button]")' in source
    assert 'document.addEventListener("click"' in source
    assert 'document.addEventListener("focusin"' in source
    assert 'playSound("startup")' in source
    for control in ["mbQuick","tbStart","tbSearch","tbTrayNet","tbTrayVoice"]:
        assert f'id="{control}"' in page, f"missing desktop control: {control}"
    assert "../aurora/assets/sounds/" in source
    sound_service=(ROOT/"desktop/aurora/aurora-event-sound.sh").read_text(encoding="utf-8")
    assert 'CHIMERA_SOUND_DIR:-$ROOT/assets/sounds' in sound_service
    live_builder=(ROOT/"live-image/build.sh").read_text(encoding="utf-8")
    assert "aurora-startup-sound.service" in live_builder
    assert "ExecStart=/usr/local/bin/aurora-event-sound startup" in live_builder
    print("Aurora audio contract: PASS (9 mapped sound events, local assets, button/focus hooks)")
if __name__=="__main__": main()
