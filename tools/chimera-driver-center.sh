#!/bin/sh
set -eu
CMD=\${1:-search}
case "$CMD" in
  search|update) exec /usr/bin/chimera-driver-manager.sh search;;
  inventory) exec /usr/bin/chimera-driver-manager.sh inventory;;
  download) shift; exec /usr/bin/chimera-driver-manager.sh download "$@";;
  install) shift; exec /usr/bin/chimera-driver-manager.sh install "$@";;
  *) echo "Usage: chimera-driver-center {search|update|inventory|install FILE}"; exit 2;;
esac
