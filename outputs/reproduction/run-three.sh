#!/bin/bash
set -euo pipefail
R=$(cd "$(dirname "$0")" && pwd)
for seed in 2026102701 2026102702 2026102703; do
  bash "$R/run-single.sh" --budget 180 --seed "$seed"
done
