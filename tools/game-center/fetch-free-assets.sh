#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; OUT="$ROOT/.local/game-assets"; mkdir -p "$OUT"
cat > "$OUT/README.txt" <<'EOF'
Chimera II Game Center asset policy
CC0-first: https://kenney.nl/assets | https://quaternius.com/ | https://kaylousberg.com/game-assets | https://polyhaven.com/ | https://ambientcg.com/
OpenGameArt: https://opengameart.org/ (mixed licenses; verify each item before packaging)
Preserve every source license/attribution file with imported assets.
EOF
echo "Asset registry created at $OUT/README.txt"
