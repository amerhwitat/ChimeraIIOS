# Chimera II Native Terminal Service

Aurora and the Native IDE share a policy-controlled local PTY service.

Architecture: Aurora / Native IDE -> Unix socket -> chimera-terminald -> approved shell adapter -> sandbox -> PTY.

Supported adapter names: bash, zsh, sh, fish, pwsh, powershell, cmd and nu when the executable exists. UI clients cannot submit arbitrary argv.

Each session receives home, tmp, work and a real SQLite database at data/chimera.sqlite3. chimera-sql uses Python's SQLite engine and denies ATTACH, DETACH and unsafe extension/schema operations.

Authentication is a bearer token. Authorization is role/capability based. Aurora and Native IDE can create/read/write/resize sessions and execute SQL, but cannot request host execution or administration.

Linux sandbox preference is bubblewrap. A root-only namespace fallback uses unshare. Without a sandbox backend the daemon refuses to spawn. Host execution is disabled unless an authorized administrator explicitly requests it.

CPU, address-space, file-size, file-descriptor and process-count limits are applied before the shell starts. The daemon listens on a local Unix socket only.

Build: `bash tools/terminal/build-terminal.sh` and `python3 -m pytest tests/terminal/test_chimera_sql.py`.
