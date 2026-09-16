#!/usr/bin/env python3
"""Optional media AI bridge for Chimera II OS.

Provides microphone recording, audio playback, speech recognition adapters,
voice-command parsing, camera capture and OpenCV/MediaPipe-oriented CV hooks.
Heavy providers remain optional so the base OS stays buildable offline.
"""
from __future__ import annotations
import argparse, json, re, wave
from pathlib import Path

COMMANDS = {
    "start recording": "record_start", "stop recording": "record_stop",
    "play audio": "play", "pause audio": "pause", "open camera": "camera_start",
    "close camera": "camera_stop", "take photo": "snapshot", "scan camera": "vision_scan",
}

def parse_voice_command(text: str) -> dict:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    action = COMMANDS.get(normalized)
    if not action:
        for phrase, candidate in COMMANDS.items():
            if phrase in normalized:
                action = candidate; break
    return {"text": text, "normalized": normalized, "action": action, "requires_confirmation": bool(action)}

def record_wav(path: Path, seconds: float, rate: int = 16000, channels: int = 1):
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("recording requires optional sounddevice and numpy") from exc
    frames = sd.rec(int(seconds * rate), samplerate=rate, channels=channels, dtype="int16")
    sd.wait()
    with wave.open(str(path), "wb") as out:
        out.setnchannels(channels); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes(np.asarray(frames, dtype=np.int16).tobytes())

def transcribe(path: Path, provider: str = "auto") -> str:
    if provider in ("auto", "whisper"):
        try:
            import whisper
            model = whisper.load_model("base")
            return model.transcribe(str(path))["text"].strip()
        except ImportError:
            if provider == "whisper": raise
    if provider in ("auto", "vosk"):
        try:
            import vosk
            raise RuntimeError("Vosk model path must be supplied by the deployment profile")
        except ImportError:
            pass
    raise RuntimeError("no speech provider installed; install Whisper or Vosk and a model")

def camera_snapshot(path: Path, camera: int = 0):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("camera support requires optional opencv-python") from exc
    cap = cv2.VideoCapture(camera)
    ok, frame = cap.read(); cap.release()
    if not ok: raise RuntimeError("camera frame capture failed")
    if not cv2.imwrite(str(path), frame): raise RuntimeError("snapshot write failed")

def vision_scan(path: Path) -> dict:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("vision support requires optional opencv-python") from exc
    img = cv2.imread(str(path))
    if img is None: raise RuntimeError("image could not be decoded")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    return {"width": int(img.shape[1]), "height": int(img.shape[0]), "channels": int(img.shape[2]), "edge_pixels": int((edges > 0).sum()), "algorithms": ["grayscale", "canny_edges"], "extensions": ["face", "object", "pose", "gesture", "ocr", "segmentation", "tracking"]}

def main() -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("command"); c.add_argument("text")
    r = sub.add_parser("record"); r.add_argument("path", type=Path); r.add_argument("seconds", type=float)
    t = sub.add_parser("transcribe"); t.add_argument("path", type=Path); t.add_argument("--provider", default="auto")
    s = sub.add_parser("snapshot"); s.add_argument("path", type=Path); s.add_argument("--camera", type=int, default=0)
    v = sub.add_parser("vision"); v.add_argument("path", type=Path)
    a = p.parse_args()
    if a.cmd == "command": print(json.dumps(parse_voice_command(a.text), ensure_ascii=False)); return 0
    if a.cmd == "record": record_wav(a.path, a.seconds); return 0
    if a.cmd == "transcribe": print(transcribe(a.path, a.provider)); return 0
    if a.cmd == "snapshot": camera_snapshot(a.path, a.camera); return 0
    if a.cmd == "vision": print(json.dumps(vision_scan(a.path))); return 0
    return 2

if __name__ == "__main__": raise SystemExit(main())
