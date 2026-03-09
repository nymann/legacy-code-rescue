#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

mkdir -p "$SKILLS_DIR"

# Symlink each skill into the global skills directory
for skill_dir in "$PLUGIN_DIR"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  ln -sf "$skill_dir" "$SKILLS_DIR/$skill_name"
  echo "  Linked skill: $skill_name"
done

chmod +x "$PLUGIN_DIR"/scripts/*.sh "$PLUGIN_DIR"/scripts/*.py

echo ""
echo "Installed to $SKILLS_DIR"
echo "Restart Claude Code to activate."
echo "Skills: /find-seam → /characterize → /mutate"
