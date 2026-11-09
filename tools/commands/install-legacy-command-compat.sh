#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:-/}"
BIN="$ROOTFS/usr/local/bin"
mkdir -p "$BIN"

install_delegate() {
  local name="$1" provider="$2" description="$3"
  local provider_path="$ROOTFS$provider"
  [[ -x "$provider_path" ]] || return 0
  cat > "$BIN/$name" <<EOF
#!/bin/sh
# $description
exec $provider "\$@"
EOF
  chmod 0755 "$BIN/$name"
  echo "[COMMAND-COMPAT] $name -> $provider"
}

# Legacy SS64 spellings with direct semantic equivalents in the installed
# Debian print stack. These wrappers delegate all arguments and exit status.
install_delegate lprintd /usr/bin/lprm "Delete print jobs using the real LPRng lprm provider."
install_delegate lprintq /usr/bin/lpq "List print jobs using the real LPRng lpq provider."
install_delegate slocate /usr/bin/plocate "Secure locate compatibility frontend using plocate."

# mkfile is a real utility with sparse and allocated-file modes. The default
# allocates/zero-fills the requested extent and sets the sticky bit, while -n
# creates a sparse file. Size suffixes follow the SS64 interface.
cat > "$BIN/mkfile" <<'PYMKFILE'
#!/usr/bin/python3
import errno
import os
import re
import stat
import sys

USAGE = "usage: mkfile [-nv] size[b|k|m|g] filename ..."

def parse_size(value):
    match = re.fullmatch(r"([0-9]+)([bBkKmMgG]?)", value)
    if not match:
        raise ValueError(f"invalid size: {value}")
    number = int(match.group(1))
    suffix = match.group(2).lower()
    scale = {"": 1, "b": 512, "k": 1024, "m": 1024**2, "g": 1024**3}[suffix]
    return number * scale

def allocate(fd, size):
    if hasattr(os, "posix_fallocate"):
        os.posix_fallocate(fd, 0, size)
    else:
        block = bytes(1024 * 1024)
        offset = 0
        while offset < size:
            chunk = block[:min(len(block), size - offset)]
            written = os.write(fd, chunk)
            if written <= 0:
                raise OSError(errno.EIO, "short write while allocating file")
            offset += written
    os.ftruncate(fd, size)

def main(argv):
    sparse = False
    verbose = False
    args = []
    for arg in argv:
        if arg == "--":
            args.extend(argv[argv.index(arg) + 1:])
            break
        if arg.startswith("-") and arg != "-":
            for flag in arg[1:]:
                if flag == "n": sparse = True
                elif flag == "v": verbose = True
                else:
                    print(USAGE, file=sys.stderr)
                    return 2
        else:
            args.append(arg)
    if len(args) < 2:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        size = parse_size(args[0])
    except ValueError as exc:
        print(f"mkfile: {exc}", file=sys.stderr)
        return 2
    status = 0
    for filename in args[1:]:
        try:
            fd = os.open(filename, os.O_CREAT | os.O_TRUNC | os.O_RDWR, 0o666)
            try:
                if sparse:
                    os.ftruncate(fd, size)
                else:
                    allocate(fd, size)
                mode = stat.S_IMODE(os.fstat(fd).st_mode) | stat.S_ISVTX
                os.fchmod(fd, mode)
            finally:
                os.close(fd)
            if verbose:
                print(f"{filename}: {size} bytes")
        except OSError as exc:
            print(f"mkfile: {filename}: {exc}", file=sys.stderr)
            status = 1
    return status

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PYMKFILE
chmod 0755 "$BIN/mkfile"
echo "[COMMAND-COMPAT] mkfile -> native Python file allocator"
