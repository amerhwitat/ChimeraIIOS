#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
if ! pkg-config --exists fuse3; then echo "SKIP: fuse3 development package unavailable"; exit 0; fi
"\${CXX:-c++}" -std=c++20 -Wall -Wextra -Werror -pthread $(pkg-config --cflags fuse3) \
 "$ROOT/userspace/hive/registry_store.cpp" "$ROOT/userspace/hive/registry_fuse.cpp" \
 $(pkg-config --libs fuse3) -o /tmp/chm-registry-mount-test
rm -f /tmp/chm-registry-mount-test
echo "PASS: FUSE registry adapter compiles"
