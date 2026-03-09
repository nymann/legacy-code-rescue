#!/usr/bin/env bash
set -euo pipefail

if [ -f pom.xml ]; then
  echo "maven"
elif [ -f build.gradle.kts ]; then
  echo "gradle-kts"
elif [ -f build.gradle ]; then
  echo "gradle"
else
  echo "Error: No pom.xml or build.gradle found in $(pwd)" >&2
  exit 1
fi
