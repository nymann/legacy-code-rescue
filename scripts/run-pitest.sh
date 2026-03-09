#!/usr/bin/env bash
set -euo pipefail

BUILD_TOOL="$1"
TARGET_CLASS="$2"
TEST_CLASS="$3"
MUTATORS="${4:-}"

case "$BUILD_TOOL" in
  maven)
    CMD=(mvn test pitest:mutationCoverage
      -DtargetClasses="$TARGET_CLASS"
      -DtargetTests="$TEST_CLASS"
      -DoutputFormats=XML
      -DtimestampedReports=false)
    if [ -n "$MUTATORS" ]; then
      CMD+=("-Dmutators=$MUTATORS")
    fi
    "${CMD[@]}"
    # Find the mutations.xml output
    REPORT=$(find target/pit-reports -name mutations.xml -maxdepth 1 2>/dev/null | head -1)
    if [ -z "$REPORT" ]; then
      echo "Error: mutations.xml not found in target/pit-reports/" >&2
      exit 1
    fi
    echo "$REPORT"
    ;;
  gradle|gradle-kts)
    GRADLE_ARGS="pitest -PpitestTargetClasses=$TARGET_CLASS -PpitestTargetTests=$TEST_CLASS"
    if [ -n "$MUTATORS" ]; then
      GRADLE_ARGS="$GRADLE_ARGS -PpitestMutators=$MUTATORS"
    fi
    ./gradlew $GRADLE_ARGS
    REPORT=$(find build/reports/pitest -name mutations.xml 2>/dev/null | head -1)
    if [ -z "$REPORT" ]; then
      echo "Error: mutations.xml not found in build/reports/pitest/" >&2
      exit 1
    fi
    echo "$REPORT"
    ;;
  *)
    echo "Error: Unknown build tool '$BUILD_TOOL'" >&2
    exit 1
    ;;
esac
