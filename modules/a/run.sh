#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export JAVA_HOME="${JAVA_HOME:-$ROOT/work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64}"
export PATH="$JAVA_HOME/bin:$PATH"
exec python3 "$ROOT/modules/a/cli.py" "$@"
