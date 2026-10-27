#!/bin/bash
set -euo pipefail
R=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$R/../.." && pwd)
export JAVA_HOME="$ROOT/work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64"
export PATH="$JAVA_HOME/bin:$PATH"
python3 "$R/audit.py"
