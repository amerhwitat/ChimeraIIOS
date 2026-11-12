#!/usr/bin/env bash
set -Eeuo pipefail

required=(mariadb psql sqlite3 redis-server redis-cli)
for command_name in "${required[@]}"; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "[DATABASE][ERROR] required provider executable is missing: $command_name" >&2
    exit 1
  }
done

mariadb --version
psql --version
sqlite3 --version
redis-server --version
redis-cli --version

for package in mariadb-server postgresql sqlite3 redis-server; do
  status="$(dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null || true)"
  [[ "$status" == "installed" ]] || {
    echo "[DATABASE][ERROR] package is not installed: $package (status: ${status:-unknown})" >&2
    exit 1
  }
done

echo "[DATABASE] MariaDB, PostgreSQL, SQLite and Redis provider binaries verified; no daemon was started."
