#!/bin/bash
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
J="$ROOT/work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64/bin"
E="$ROOT/work/DiffTGen/lib/evosuite-1.0.2.jar"
"$J/javap" -classpath "$E" -c -private org.evosuite.utils.Randomness
"$J/javap" -classpath "$E" -c -private org.evosuite.Properties
