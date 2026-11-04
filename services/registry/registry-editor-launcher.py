#!/usr/bin/env python3
"""Start the unprivileged registry editor API and open its capability URL."""
import os
import pathlib
import stat
import subprocess
import sys
import time
import webbrowser

RUNTIME = pathlib.Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
TOKEN_PATH = RUNTIME / "chimera-registry-editor.token"
API_PATH = "/usr/lib/chimera/registry/registry-editor-api.py"


def read_token():
    try:
        st = TOKEN_PATH.stat()
        if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:
            raise PermissionError("unsafe editor token permissions")
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
        return token if len(token) >= 32 else None
    except FileNotFoundError:
        return None


def wait_for_token():
    for _ in range(50):
        token = read_token()
        if token:
            return token
        time.sleep(0.1)
    return None


def main():
    # Prefer the user manager when one is present, but support kiosk sessions
    # launched by a system unit without a systemd --user manager.
    service = subprocess.run(
        ["systemctl", "--user", "start", "chimera-registry-editor.service"],
        capture_output=True, text=True, check=False)
    token = wait_for_token()
    if not token:
        try:
            subprocess.Popen(
                [sys.executable, API_PATH],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True)
        except OSError as exc:
            print(f"cannot start registry editor API: {exc}", file=sys.stderr)
            return 1
        token = wait_for_token()
    if not token:
        detail = service.stderr.strip() or "API did not publish a runtime capability"
        print("registry editor service did not start: " + detail, file=sys.stderr)
        return 1
    webbrowser.open("http://127.0.0.1:8765/#" + token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
