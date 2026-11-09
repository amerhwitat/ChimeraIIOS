# Aurora local terminal bridge

The browser terminal remains a safe in-memory shell by default. To connect it to a local
Chimera II OS or OctavianOS machine, start:
python3 tools/runtime/chimera-terminal-backend.py

Copy the one-time bearer token printed by the server into Aurora Terminal's Local Bridge
settings, use http://127.0.0.1:8767, and select Connect. The server binds only to loopback,
checks the GitHub Pages Origin and Host, requires the token, limits request sizes and
command rates, and confines safe-mode file operations to a dedicated workspace.

Safe mode supports navigation, listing, reading/writing workspace files, metadata commands,
and a small reviewed command set. It never invokes a shell or runs arbitrary commands.
For a full local shell, the user must deliberately start the server with --unsafe-shell.
That mode runs the selected installed shell as the local user and can access files and
resources available to that account. Only enable it when the page and machine are trusted.
The token is not a sandbox and does not protect against a compromised trusted origin.

The backend does not install shells, download binaries, expose a public listener, or execute
commands on GitHub Pages servers. Use a disposable VM/container for untrusted code.
