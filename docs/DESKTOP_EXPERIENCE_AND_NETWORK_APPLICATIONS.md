## Desktop Experience and Network Applications

### Shared desktop behavior

The Aurora Wayland Glass and Marine Desktop front ends load the shared desktop experience runtime. It supplies a glass/3D-styled panel bar and common interaction behavior without claiming that a browser preview is a native Wayland compositor.

- Right-click a desktop shortcut for Open, Rename, Properties, Pin and Remove.
- Single click selects; a second click on the selected item starts inline rename after the double-click window.
- Double-click opens the selected item.
- F2 renames the selected item; Alt+Enter opens Properties; Delete removes a selected shortcut after confirmation.
- Ctrl+Alt+E opens Applications; Ctrl+Alt+N opens Network Apps; Ctrl+Alt+V opens VoiceConnect project; Ctrl+Alt+S opens Settings; Ctrl+Alt+D opens Desktop Profiles.
- Ctrl+Alt+F opens Files; Ctrl+Alt+T opens Terminal; Ctrl+Alt+B opens Browser. Ctrl+Shift+N creates a shortcut through the existing shortcut manager. Meta/Command modifiers are accepted on macOS; Ctrl modifiers work on Windows and Linux.
- The top-right panel buttons remain visible as desktop-level icons/actions.

The profile set now includes Aurora Glass (macOS-inspired), Marine Fluent (Windows-inspired) and Nebula Linux Workspace (Plasma-inspired), with original artwork and styling rather than copied proprietary assets. The shared UI uses layered gradients, depth, shadows and motion without claiming parity with proprietary OS internals.

### Network Applications Panel

desktop/shared/network-applications.html and network-applications.json catalogue browsers, email, messaging, video calls, remote access, VPN, file sync, diagnostics, network configuration and device integration. Upstream URLs and license identifiers are catalogue metadata, not evidence of installation. Launch requests are conditional on local desktop handlers. Network scanners and packet analyzers are for authorized networks only.

The panel is installed in the live image at /opt/aurora/desktop/shared/ and exposed from the Openbox menu and desktop panel bar.

### VoiceConnect integration boundary

VoiceConnect is connected as a project entry pointing to https://github.com/amerhwitat/test. Its source repository contains the Electron/WebRTC application and cross-platform packaging workflows. The desktop entry invokes a safe launcher that starts a locally installed VoiceConnect binary when present and otherwise opens the project page. It is not a bundled native VoiceConnect executable. Bundling the app requires a successful exact-head build artifact and validation of its GUI/click tests. Physical-device calls, TURN, signing, production deployment and independent review remain separate acceptance gates.

### Repository SDK build discovery

tools/build-repository-sdks.sh discovers first-party CMake, Cargo, Go, Maven, npm build-script and Gradle wrapper projects. It excludes vendored snapshots and generated/dependency directories, records PASS/FAIL/SKIP in build/sdk-build/sdk-build-results.tsv, and writes detailed logs. The main Chimera ISO script invokes it before ISO composition; live-image builders invoke it before staging the desktop. Optional SDK failures are recorded but do not mask the ISO pipeline by default. Set CHIMERA_SDK_BUILD_STRICT=1 to make a discovered SDK build failure fatal, or CHIMERA_BUILD_REPO_SDKS=0 to skip discovery.

### Verification boundary

Static contract tests and CI syntax/build checks are not substitutes for desktop interaction tests under the actual live image. The ISO workflow must validate the packaged desktop assets and run the graphical/QEMU tests before publication. No ISO release or production-ready desktop claim is implied by adding these source files.
