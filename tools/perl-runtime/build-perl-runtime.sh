#!/usr/bin/env bash
set -euo pipefail

# Reproducible host-compatibility build of upstream Perl. This does NOT claim
# that the result is executable by the native Koronos kernel.
VERSION="5.44.0"
CHANNEL="stable"
ARCHIVE_NAME=""
ARCHIVE_URL=""
SHA256=""
select_version() {
  case "$1" in
    stable|5.44.0)
      VERSION="5.44.0"; CHANNEL="stable"
      SHA256="3b855066b92491cb40e86affb1ca57d1a388aa43e51b91c7806a32c2f65f96c3"
      ;;
    development|5.45.3)
      VERSION="5.45.3"; CHANNEL="development"
      SHA256="f8aac25c3dc34abbaf0d84da132913f726c7faa27906b460cc442da417c2fdac"
      ;;
    *) echo "[perl-runtime] ERROR: unsupported version/channel: $1 (use stable or development)" >&2; exit 2 ;;
  esac
  ARCHIVE_NAME="perl-${VERSION}.tar.gz"
  ARCHIVE_URL="https://www.cpan.org/src/5.0/${ARCHIVE_NAME}"
}
select_version "$VERSION"

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${PERL_BUILD_DIR:-$ROOT/build/perl-runtime}"
PREFIX=""
ARCHIVE=""
JOBS="${PERL_BUILD_JOBS:-2}"

usage() {
  cat <<'USAGE'
Usage: tools/perl-runtime/build-perl-runtime.sh [--version stable|development] [--prefix DIR] [--work-dir DIR] [--archive FILE]

Builds upstream Perl from a SHA-256-pinned CPAN source archive (stable 5.44.0
by default; development 5.45.3 is optional), runs upstream tests, stages the
interpreter, and runs the repository smoke test. This builds for the host ABI;
it is not a native Koronos executable until compatible POSIX/libc support exists.
USAGE
}
while (($#)); do
  case "$1" in
    --version) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; select_version "$2"; shift 2 ;;
    --prefix) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; PREFIX="$2"; shift 2 ;;
    --work-dir) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; WORK_DIR="$2"; shift 2 ;;
    --archive) [[ $# -ge 2 ]] || { usage >&2; exit 2; }; ARCHIVE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[perl-runtime] ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ -n "$PREFIX" ]] || PREFIX="$ROOT/build/perl-${VERSION}-rootfs"

for cmd in make cc tar; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[perl-runtime] ERROR: missing required command: $cmd" >&2; exit 2; }
done
if command -v sha256sum >/dev/null 2>&1; then
  sha256_file() { sha256sum "$1" | awk '{print $1}'; }
elif command -v shasum >/dev/null 2>&1; then
  sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }
else
  echo "[perl-runtime] ERROR: sha256sum or shasum is required" >&2; exit 2
fi

mkdir -p "$WORK_DIR/downloads" "$WORK_DIR/src" "$(dirname -- "$PREFIX")"
if [[ -z "$ARCHIVE" ]]; then
  ARCHIVE="$WORK_DIR/downloads/$ARCHIVE_NAME"
  if [[ ! -f "$ARCHIVE" ]]; then
    if command -v curl >/dev/null 2>&1; then
      curl --fail --location --retry 3 --output "$ARCHIVE" "$ARCHIVE_URL"
    elif command -v wget >/dev/null 2>&1; then
      wget --tries=3 --output-document="$ARCHIVE" "$ARCHIVE_URL"
    else
      echo "[perl-runtime] ERROR: curl or wget is required to download Perl" >&2; exit 2
    fi
  fi
fi
[[ -f "$ARCHIVE" ]] || { echo "[perl-runtime] ERROR: source archive not found: $ARCHIVE" >&2; exit 2; }
ACTUAL_SHA="$(sha256_file "$ARCHIVE")"
[[ "$ACTUAL_SHA" == "$SHA256" ]] || {
  echo "[perl-runtime] ERROR: SHA-256 mismatch for $ARCHIVE_NAME" >&2
  echo "expected: $SHA256" >&2
  echo "actual:   $ACTUAL_SHA" >&2
  exit 2
}

SRC_DIR="$WORK_DIR/src/perl-$VERSION"
rm -rf "$SRC_DIR"
mkdir -p "$SRC_DIR"
tar -xzf "$ARCHIVE" --strip-components=1 -C "$SRC_DIR"
cd "$SRC_DIR"
echo "[perl-runtime] Configuring Perl $VERSION ($CHANNEL) for host ABI; prefix=$PREFIX"
CONFIGURE_FLAGS=(-des -Dprefix="$PREFIX" -Dman1dir=none -Dman3dir=none -Duseshrplib=false)
# Upstream Perl deliberately requires an explicit opt-in for odd-numbered
# development releases. Keep this flag scoped to the opt-in development channel.
if [[ "$CHANNEL" == "development" ]]; then
  CONFIGURE_FLAGS+=(-Dusedevel)
fi
./Configure "${CONFIGURE_FLAGS[@]}"
make -j"$JOBS"
make test
make install

PERL_BIN="$PREFIX/bin/perl"
[[ -x "$PERL_BIN" ]] || { echo "[perl-runtime] ERROR: installed interpreter missing: $PERL_BIN" >&2; exit 2; }
"$PERL_BIN" -e 'use strict; use warnings; print "Perl $] host-runtime smoke OK\n";'
"$PERL_BIN" "$ROOT/tools/perl-runtime/perl-runtime-smoke.pl"
echo "[perl-runtime] PASS: Perl $VERSION ($CHANNEL) built, tested, and installed to $PREFIX"
echo "[perl-runtime] NOTE: host-ABI build only; native Koronos execution remains gated on libc/POSIX syscall support."
