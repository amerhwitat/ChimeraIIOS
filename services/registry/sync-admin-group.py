#!/usr/bin/env python3
"""Grant CHMRG01 write access only to local sudo administrators."""
import grp
import pwd
import os
import subprocess
import sys

def main():
    if os.geteuid() != 0:
        print("registry-admin group sync requires root", file=sys.stderr)
        return 2
    try:
        admin = grp.getgrnam("chimera-admin")
    except KeyError:
        result = subprocess.run(["groupadd", "--system", "chimera-admin"], check=False,
                                capture_output=True, text=True)
        if result.returncode:
            print("could not create chimera-admin group:", result.stderr, file=sys.stderr)
            return result.returncode
        admin = grp.getgrnam("chimera-admin")
    try:
        sudo = grp.getgrnam("sudo")
    except KeyError:
        return 0
    members = set(sudo.gr_mem)
    members.update(entry.pw_name for entry in pwd.getpwall()
                   if entry.pw_gid == sudo.gr_gid and entry.pw_uid >= 1000)
    for account in sorted(members):
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
