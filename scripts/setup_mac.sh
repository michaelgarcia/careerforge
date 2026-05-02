#!/usr/bin/env bash
# CareerForge Setup — macOS
# Run with: ./scripts/setup_mac.sh
#
# What this script installs:
#   1. Homebrew    — package manager for macOS (https://brew.sh)
#   2. Git         — for cloning repositories
#   3. Python 3.11+ — all scripting (docx generation, LinkedIn scanning, scoring)
#   4. Python packages — python-docx, httpx, pydantic, pyyaml, beautifulsoup4, markdown, weasyprint
#   5. Claude Desktop — checked but not auto-installed (manual step)

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ALL_OK=true

echo ""
echo "============================================================"
echo "  CareerForge Setup"
echo "============================================================"
echo "  This script will check and install:"
echo "    [1] Homebrew (package manager)"
echo "    [2] Git"
echo "    [3] Python 3.11+"
echo "    [4] Python packages (python-docx, httpx, pydantic, ...)"
echo "    [5] Claude Desktop (check only)"
echo "------------------------------------------------------------"
echo ""

# ── Helper ──────────────────────────────────────────────────────────────────

print_ok()   { printf "  [%s] %-30s ${GREEN}[OK]${NC} %s\n" "$1" "$2" "$3"; }
print_inst() { printf "  [%s] %-30s ${CYAN}[INSTALLED]${NC} %s\n" "$1" "$2" "$3"; }
print_warn() { printf "  [%s] %-30s ${YELLOW}[NOT FOUND]${NC} %s\n" "$1" "$2" "$3"; }
print_fail() { printf "  [%s] %-30s ${RED}[FAILED]${NC} %s\n" "$1" "$2" "$3"; }
print_skip() { printf "  [%s] %-30s ${YELLOW}[SKIPPED]${NC} %s\n" "$1" "$2" "$3"; }

# ── Step 1: Homebrew ─────────────────────────────────────────────────────────

if command -v brew &>/dev/null; then
    BREW_VER=$(brew --version 2>/dev/null | head -1 | sed 's/Homebrew //')
    print_ok "1/5" "Homebrew" "$BREW_VER"
else
    print_warn "1/5" "Homebrew" ""
    echo "       Homebrew is required to install Git and Python." >&2
    echo "       Install it by running this command in your terminal:" >&2
    echo "" >&2
    echo "         /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" >&2
    echo "" >&2
    echo "       Then re-run: ./scripts/setup_mac.sh" >&2
    ALL_OK=false
    echo ""
    echo "============================================================"
    echo "  Setup stopped — Homebrew must be installed first."
    echo "  See instructions above, then re-run this script."
    echo "============================================================"
    echo ""
    exit 1
fi

# ── Step 2: Git ──────────────────────────────────────────────────────────────

if command -v git &>/dev/null; then
    GIT_VER=$(git --version 2>/dev/null | sed 's/git version //')
    print_ok "2/5" "Git" "$GIT_VER"
else
    printf "  [2/5] %-30s ${YELLOW}[INSTALLING...]${NC}\n" "Git"
    if brew install git 2>&1 | tail -1 | grep -q "already installed"; then
        :
    fi
    if command -v git &>/dev/null; then
        GIT_VER=$(git --version 2>/dev/null | sed 's/git version //')
        print_inst "2/5" "Git" "$GIT_VER"
    else
        print_fail "2/5" "Git" ""
        echo "       Manual install: brew install git" >&2
        echo "       Or download: https://git-scm.com/downloads" >&2
        ALL_OK=false
    fi
fi

# ── Step 3: Python 3.11+ ─────────────────────────────────────────────────────

PYTHON_CMD=""
for cmd in python3.11 python3.12 python3.13 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        MAJ=$(echo "$VER" | cut -d. -f1)
        MIN=$(echo "$VER" | cut -d. -f2)
        if [ "${MAJ:-0}" -gt 3 ] || { [ "${MAJ:-0}" -eq 3 ] && [ "${MIN:-0}" -ge 11 ]; }; then
            PYTHON_CMD="$cmd"
            PYTHON_VER="$VER"
            break
        fi
    fi
done

if [ -n "$PYTHON_CMD" ]; then
    print_ok "3/5" "Python 3.11+" "$PYTHON_VER"
else
    printf "  [3/5] %-30s ${YELLOW}[INSTALLING...]${NC}\n" "Python 3.11+"
    brew install python@3.11 2>&1 | grep -E "^(==>|Error)" || true
    # Refresh PATH for brew-installed python
    BREW_PREFIX=$(brew --prefix 2>/dev/null || echo "/usr/local")
    export PATH="$BREW_PREFIX/bin:$PATH"
    for cmd in python3.11 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
            MAJ=$(echo "$VER" | cut -d. -f1)
            MIN=$(echo "$VER" | cut -d. -f2)
            if [ "${MAJ:-0}" -gt 3 ] || { [ "${MAJ:-0}" -eq 3 ] && [ "${MIN:-0}" -ge 11 ]; }; then
                PYTHON_CMD="$cmd"
                PYTHON_VER="$VER"
                break
            fi
        fi
    done
    if [ -n "$PYTHON_CMD" ]; then
        print_inst "3/5" "Python 3.11+" "$PYTHON_VER"
    else
        print_fail "3/5" "Python 3.11+" ""
        echo "       Manual install: brew install python@3.11" >&2
        echo "       Or download: https://www.python.org/downloads" >&2
        ALL_OK=false
    fi
fi

# ── Step 4: Python packages ───────────────────────────────────────────────────

if [ -n "$PYTHON_CMD" ]; then
    printf "  [4/5] %-30s ${YELLOW}[INSTALLING...]${NC}\n" "Python packages"
    PACKAGES="python-docx httpx pydantic pyyaml beautifulsoup4 markdown weasyprint"
    if $PYTHON_CMD -m pip install --quiet $PACKAGES 2>/dev/null; then
        print_ok "4/5" "Python packages" "python-docx, httpx, pydantic, pyyaml, bs4, markdown, weasyprint"
    else
        # Try with --break-system-packages for newer Python on Mac
        if $PYTHON_CMD -m pip install --quiet --break-system-packages $PACKAGES 2>/dev/null; then
            print_ok "4/5" "Python packages" "python-docx, httpx, pydantic, pyyaml, bs4, markdown, weasyprint"
        else
            print_fail "4/5" "Python packages" ""
            echo "       Try manually: $PYTHON_CMD -m pip install $PACKAGES" >&2
            echo "       If you see 'externally-managed-environment', add --break-system-packages" >&2
            ALL_OK=false
        fi
    fi
else
    print_skip "4/5" "Python packages" "(Python not available)"
    ALL_OK=false
fi

# ── Step 5: Claude Desktop ────────────────────────────────────────────────────

if command -v claude &>/dev/null; then
    CLAUDE_VER=$(claude --version 2>/dev/null | head -1 || echo "installed")
    print_ok "5/5" "Claude Desktop" "$CLAUDE_VER"
else
    print_warn "5/5" "Claude Desktop" ""
    echo "       Download and install from: https://claude.com/download"
    echo "       After installing, re-run this script or proceed to launch."
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
if [ "$ALL_OK" = true ]; then
    printf "  ${GREEN}Setup complete!${NC}\n"
    echo ""
    echo "  To start CareerForge:"
    echo "    ./scripts/launch_mac.command"
    echo "    Or type: claude  (from this directory)"
else
    printf "  ${YELLOW}Setup finished with issues (see [FAILED] steps above).${NC}\n"
    echo ""
    echo "  Fix the failed steps manually using the links shown above,"
    echo "  then re-run ./scripts/setup_mac.sh to confirm everything is ready."
fi
echo "============================================================"
echo ""
