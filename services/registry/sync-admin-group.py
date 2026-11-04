#!/usr/bin/env python3
"""Grant the local registry-admin group only to existing sudo administrators."""
import grp
import subprocess
import sys

def main():
    try:
        members = sorted(set(grp.getgrnam("sudo").gr_mem))
    except KeyError:
        members = []
    for account in members:
        if not account or account.startswith("-"):
            continue
        result = subprocess.run(["usermod", "-aG", "chimera-admin", account],
                                check=False, capture_output=True, text=True)
        if result.returncode:
            print("registry-admin group sync failed for", account, result.stderr, file=sys.stderr)
            return result.returncode
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
