# Voice and Speech Subsystem

Chimera II now exposes a stable speech abstraction for TTS and a corresponding recognition boundary for future STT.

## Providers

- Windows: SAPI/WinRT adapter boundary.
- Linux/Unix: Speech Dispatcher, PipeWire/audio-session integration, and ALSA/PulseAudio compatibility boundaries.
- Apple: AVFoundation/CoreAudio boundary.
- External: opt-in local or remote engines through an explicit provider interface.

The core does not silently upload text or audio. A provider must be selected and policy-approved. Language/locale, rate, pitch and volume are explicit request fields.

The voice layer is intentionally separate from the neural reasoning engine: reasoning produces a response; voice renders it. This preserves auditability and allows accessibility modes without changing inference.
