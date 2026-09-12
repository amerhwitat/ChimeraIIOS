"""Cross-platform voice abstraction for Chimera II OS.

The core does not bundle proprietary speech engines. Platform providers can implement
`speak` and `recognize` using Windows SAPI/WinRT, Linux Speech Dispatcher/PipeWire,
macOS AVFoundation/CoreAudio, or an explicitly configured external service.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class VoiceRequest:
    text: str
    language: str = "en"
    rate: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0

class VoiceBackend(Protocol):
    def speak(self, request: VoiceRequest) -> None: ...

class NullVoiceBackend:
    def speak(self, request: VoiceRequest) -> None:
        if not request.text:
            raise ValueError("empty text")

class VoiceEngine:
    def __init__(self, backend: VoiceBackend | None = None):
        self.backend = backend or NullVoiceBackend()
    def speak(self, text: str, language: str = "en", rate: float = 1.0) -> None:
        self.backend.speak(VoiceRequest(text=text, language=language, rate=rate))
