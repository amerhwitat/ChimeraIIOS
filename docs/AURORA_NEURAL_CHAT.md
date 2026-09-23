# Aurora Chimera Neural Chat

Aurora Wayland Glass now exposes a dedicated Chimera Neural Chat application surface.

## Architecture

Aurora -> Chimera Neural Chat -> stable Koronos IPC -> neural/trusted-node layer.

The initial native client uses the existing chm::neural::reason() evidence model and is intentionally deterministic. A production inference adapter can replace the response provider without changing the Aurora application contract.

## VoiceConnect replacement

Historical DirectX documentation identifies VoiceConnect as a DirectPlay Voice sample. It initialized voice audio, created a voice session, connected a client, and managed transmit targets. Microsoft documents DirectPlay Voice as deprecated.

Chimera's replacement is not copied from or linked against the legacy DirectX implementation. voice/cpp/src/voiceconnect.cpp is a clean-room, DirectX-independent transport implementation using POSIX UDP and PCM16 frames. Audio capture/playback remains an adapter boundary for PipeWire, ALSA, WASAPI, CoreAudio, or another approved provider.

This avoids DirectX 8/9, DirectPlay, DirectSound, and legacy Managed DirectX dependencies.

## Aurora integration

The application is registered as chimera-neural-chat and its Wayland Glass surface is described by desktop/aurora/chimera-neural-chat.desktop.json.

## Security

Voice is opt-in. The transport does not capture microphone audio by itself. A future PipeWire adapter should request explicit portal/session permission before opening an input device.
