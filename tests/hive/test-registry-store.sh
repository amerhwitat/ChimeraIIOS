#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Werror -pthread "$ROOT/userspace/hive/registry_store.cpp" "$ROOT/tests/hive/test_registry_store.cpp" -o "$TMP/test"
"$TMP/test"
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Werror -pthread "$ROOT/userspace/hive/registry_store.cpp" "$ROOT/userspace/hive/registryctl.cpp" -o "$TMP/chm-registry"
"$TMP/chm-registry" --db "$TMP/db" set test/key value
test "$("$TMP/chm-registry" --db "$TMP/db" get test/key)" = value
"$TMP/chm-registry" --db "$TMP/db" compact
echo "PASS: Hive registry transactions, recovery, CLI and checkpoint"