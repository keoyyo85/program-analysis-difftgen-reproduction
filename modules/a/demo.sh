#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/outputs/a/teaching-$(date +%Y%m%d-%H%M%S)"
bash "$ROOT/modules/a/run.sh" --request "$ROOT/examples/teaching/int-threshold/request.json" --output "$OUT"
python3 "$ROOT/interfaces/mock_b.py" --input "$OUT/analysis.json" --output "$OUT/b-mock.json"
echo "Teaching mechanism only; no real execution or detection-rate claim: $OUT"
