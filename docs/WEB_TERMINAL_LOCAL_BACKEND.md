# Aurora local terminal bridge

The GitHub Pages shell lab is browser-only until a local bridge is started. The bridge binds only to loopback and defaults to a workspace-confined command set.

## Start

Chimera II OS:
```sh
python3 tools/runtime/chimera-terminal-backend.py --profile chimera
```

OctavianOS:
```sh
python3 vendor/chimera-ii-os/source/tools/runtime/chimera-terminal-backend.py --profile octavian
```

The server prints a one-time bearer token. In the web terminal, use `http://127.0.0.1:8767`, paste the token, and connect. Shell profiles include Bash, Zsh, Fish, CMD, PowerShell and Chimera.

## Safe mode (default)

Safe mode does not invoke a host shell. It implements reviewed workspace commands: `pwd`, `cd`, `ls`, `cat`, `echo`, `whoami`, `hostname`, `uname`, `date`, `env`, `which`, `mkdir`, `touch`, `rm`, `clear` and `help`. File access is confined to the configured workspace; path traversal and symlink escapes are rejected.

## Full local shell (opt-in)

To enable actual installed shells, start with `--unsafe-shell`. Commands then run with the same local-user privileges as the bridge process. This is not a sandbox; use only with trusted pages/software, preferably in a disposable VM/container. Missing selected shells are reported rather than silently substituted.

## Controls

- Loopback-only bind: `127.0.0.1`.
- Bearer token required for capabilities and command requests.
- CORS restricted to `https://amerhwitat.github.io` and localhost development origins.
- Private Network Access preflight supported.
- Request size, command length, execution time and output are bounded.
- Commands run only on the machine where the bridge is started, never on GitHub Pages.
