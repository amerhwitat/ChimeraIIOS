# Mobile build automation

The mobile build layer is intended to be reproducible on Windows, with PowerShell and batch entry points. `install-android-sdk.ps1` installs the Android Command-line Tools and required SDK packages when they are absent; `build-all-mobile.ps1` then builds debug/release APKs.

The scripts use Google's published Android command-line tools distribution and `sdkmanager`. Android's current documentation recommends the Android CLI for SDK package management; `sdkmanager` remains provided with the command-line tools for compatibility. Pinning a command-line-tools archive and SDK/build-tools versions makes automated builds more deterministic.

## Commands

```powershell
.\install-android-sdk.ps1
.\build-all-mobile.ps1
```

or:

```bat
build-all-mobile.cmd
```

## Communications architecture

The mobile applications expose a common communications boundary for authenticated opt-in:

- IRC-style text channels and presence/events.
- WebSocket/TCP transport adapters.
- Voice chat using device microphone and speaker through a real-time media layer.
- Video chat using the camera when permission is granted.
- Camera/microphone capability detection and runtime permission handling.
- Conversation/event synchronization using node identity, sequence numbers, payload hashes and replay protection.
- Shared BizX/BizXtreme conversation identifiers so authorized participants can synchronize channel history and session state.

The application does not perform unsolicited Internet scanning, silently activate microphone/camera hardware, exchange credentials, or accept arbitrary remote executable commands. All microphone/camera use is user-visible and permission-controlled.

For production voice/video, use a maintained WebRTC media stack rather than implementing a media codec or congestion-control protocol from scratch. Signaling and synchronized chat state remain separate from the media transport.

## Verification

The build scripts must be run on a host with network access and JDK 17+. They fail rather than claiming success when required tooling is missing. APK paths are reported after Gradle completes.
