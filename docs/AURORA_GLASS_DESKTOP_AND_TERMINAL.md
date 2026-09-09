# Aurora Wayland Glass Desktop & Terminal

## Purpose

Chimera II now treats Aurora Wayland Glass as a single desktop surface shared by the native Wayland environment and the Web UI. The Web UI is a desktop shell, not a collection of unrelated pages.

## Visual contract

The approved Aurora Wayland Glass Desktop artwork from the project Library is the canonical visual reference. The production web/native implementation uses the same wallpaper, glass proportions, rounded window geometry, blue/purple accent language, top bar, left dock, right information rail, centered bottom dock, and translucent application surfaces.

The reference composition includes a scenic mountain/lake background, translucent glass panels, Aurora Wayland branding, left-side application dock, right-side widgets, and a glass terminal window. The Chimera II showcase additionally establishes the terminal/system-monitor presentation and Aurora desktop branding. See the project Library images for the visual source of truth.

## Web desktop surface

`web/aurora_shell.js` initializes the Aurora desktop and loads:

- `aurora_glass_desktop.css`
- `aurora_desktop_surface.js`
- `aurora_glass_desktop.json`
- `aurora_apps.json`

Local Aurora applications are opened as managed desktop windows on the surface. External web destinations remain separate windows. This gives the browser implementation the same application-surface model as the native desktop without pretending that a browser can create unrestricted native Wayland surfaces.

Each embedded application is isolated in a constrained frame. Native execution remains behind the authorized session/backend boundary.

## Native Aurora

The native stack remains:

`DRM/KMS → Mesa/Vulkan/OpenGL → Aurora compositor → Wayland clients`

The native compositor owns real Wayland surfaces, input routing, frame scheduling, blur/post-processing and window placement. The Web UI mirrors this model with a browser desktop canvas and managed application windows.

## Terminal

The terminal contract is `web/aurora_terminal_profile.json`.

The visual profile uses:

- JetBrains Mono with Cascadia Code/Fira Code fallback
- dark translucent surface
- backdrop blur
- rounded glass window chrome
- blue/purple accents
- `aurora@chimera:~$` prompt
- `man`, `apropos`, and `whatis`
- command history/completion/aliases
- POSIX/Linux/BSD/System V/Bash/Zsh commands
- Windows CMD and PowerShell command families
- Chimera-specific commands

The complete command reference is `web/command_catalog.json`; the manual database is `web/man_pages.json`.

## Command families

The unified terminal catalog covers files/text, processes, memory, storage, kernel/services/logs, networking, DNS/DHCP, sockets, packet diagnostics, routing/firewall, namespaces, security observation, Bash/Zsh/POSIX, Windows CMD, PowerShell, compilers/build systems, debugging, ISA tooling, Aurora desktop control, installer management, health/KPI monitoring, crash recovery and Chimera runtime services.

Security-oriented commands are documentation/observation entries and must execute only through authorized lab adapters.

## `man` model

`man <page>` reads the machine-readable manual database. `apropos <keyword>` searches descriptions and `whatis <command>` returns a one-line description. The database is intentionally original metadata and concise operational guidance; it does not vendor copyrighted manuals wholesale.

## Cross-platform parity

The same logical contracts are referenced by CPU4096Simulator and the associated research repositories. Platform-specific backends can implement native execution while preserving the same Aurora visual and command schemas.

## Background asset requirement

The repository expects the approved artwork at `web/assets/aurora/aurora-wallpaper.png` (and `public/assets/aurora/aurora-wallpaper.png` in the simulator). The Library artwork is the authoritative reference. If a deployment does not contain the approved binary asset, it must not claim pixel-identical background parity; it should report the missing asset and use the configured fallback only until the canonical asset is installed.
