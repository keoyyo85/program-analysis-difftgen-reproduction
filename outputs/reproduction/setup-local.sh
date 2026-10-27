#!/usr/bin/env bash
set -euo pipefail
REP=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$REP/../.." && pwd)
DEPS="$ROOT/work/deps"
if [ ! -x "$DEPS/zulu8.94.0.17-ca-jdk8.0.492-linux_x64/bin/javac" ]; then
  tar -xzf "$DEPS/jdk8-complete.tar.gz" -C "$DEPS"
fi
mkdir -p "$DEPS/ant/bin" "$DEPS/ant/lib"
cp "$DEPS/ant.jar" "$DEPS/ant/lib/ant.jar"
cp "$DEPS/ant-launcher.jar" "$DEPS/ant/lib/ant-launcher.jar"
cp "$DEPS/ant-junit.jar" "$DEPS/ant/lib/ant-junit.jar"
cat > "$DEPS/ant/bin/ant" <<'EOF'
#!/bin/sh
exec "$JAVA_HOME/bin/java" -Dant.home="$ANT_HOME" -classpath "$ANT_HOME/lib/ant-launcher.jar" org.apache.tools.ant.launch.Launcher "$@"
EOF
chmod +x "$DEPS/ant/bin/ant"
