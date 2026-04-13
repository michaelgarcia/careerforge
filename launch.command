#!/usr/bin/env bash
# Double-click this file to open CareerForge in Claude Code.
# First time on Mac: right-click → Open to bypass Gatekeeper, then double-click works normally.
cd "$(dirname "$0")"
if ! command -v claude &>/dev/null; then
  echo "Claude Code not found. Install from: https://claude.ai/code"
  read -r -p "Press Enter to close..."
  exit 1
fi
claude
