#!/usr/bin/env bash
set -e

echo "=== CareerForge Setup ==="
echo ""

# Node.js check
if ! command -v node &>/dev/null; then
  echo "Node.js not found. Install from https://nodejs.org (v18+) then re-run this script."
  exit 1
fi
NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VER" -lt 18 ]; then
  echo "Node.js v18+ required (found $(node --version)). Update at https://nodejs.org"
  exit 1
fi
echo "✓ Node.js $(node --version)"

# Python check
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "Python not found. Install Python 3.11+ from https://www.python.org then re-run."
  exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo "✓ Python $($PYTHON --version)"

# Node deps
echo ""
echo "Installing Node.js dependencies..."
npm install

# Python deps
echo "Installing Python dependencies..."
$PYTHON -m pip install -r requirements.txt --quiet

# Claude Code check
if ! command -v claude &>/dev/null; then
  echo ""
  echo "Claude Code not found. Install it from: https://claude.ai/code"
  echo "Then run: ./launch.command (or type 'claude' in this directory)"
else
  echo "✓ Claude Code $(claude --version 2>/dev/null || echo 'installed')"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start CareerForge:"
echo "  Mac/Linux: double-click launch.command, or type 'claude' in this directory"
echo "  Windows:   double-click launch.bat"
