#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.claude/plugins/local"

mkdir -p "$TARGET_DIR"
ln -sf "$PLUGIN_DIR" "$TARGET_DIR/mutation-skill"
chmod +x "$PLUGIN_DIR"/scripts/*.sh "$PLUGIN_DIR"/scripts/*.py

echo "Installed legacy-code-rescue plugin → $TARGET_DIR/mutation-skill"
echo "Restart Claude Code to activate."
echo "Commands: /find-seam → /characterize → /mutate"
