#!/usr/bin/env bash
set -euo pipefail
REP=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$REP/../.." && pwd)
export JAVA_HOME="$ROOT/work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64"
export ANT_HOME="$ROOT/work/deps/ant"
export PATH="$JAVA_HOME/bin:$ANT_HOME/bin:$PATH"
export JAVA_TOOL_OPTIONS='-Xmx1024m -XX:ActiveProcessorCount=2'
export OMP_NUM_THREADS=2
exec python3 "$REP/driver.py" "$@"
