#!/usr/bin/env bash
set -euo pipefail

# Cyberzard installer — creates a user-local venv and links the CLI into ~/.local/bin
# Usage:
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
# Optional extras (openai|anthropic):
#   CYBERZARD_EXTRAS=openai bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"

REPO_URL="https://github.com/elwizard33/Cyberzard.git"
INSTALL_ROOT="${CYBERZARD_HOME:-$HOME/.local/share/cyberzard}"
REPO_DIR="$INSTALL_ROOT/Cyberzard"
VENV_DIR="$INSTALL_ROOT/.venv"
BIN_DIR="$HOME/.local/bin"
EXTRAS="${CYBERZARD_EXTRAS:-}"

echo "==> Cyberzard installer"

# Pick Python (prefer newer, accept 3.10+)
PY=""
for c in python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "ERROR: Python 3.10+ is required. Please install python3 first." >&2
  exit 1
fi

# Ensure venv module exists
if ! "$PY" -c "import venv" >/dev/null 2>&1; then
  echo "ERROR: Python venv module missing. On Ubuntu: sudo apt-get install -y python3-venv" >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"

echo "==> Fetching Cyberzard repo"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only --no-rebase --quiet || git -C "$REPO_DIR" pull --ff-only --quiet
else
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi

echo "==> Creating virtualenv ($VENV_DIR)"
if [ ! -f "$VENV_DIR/bin/activate" ]; then
  "$PY" -m venv "$VENV_DIR"
fi

echo "==> Upgrading pip/setuptools/wheel"
"$VENV_DIR/bin/python" -m pip install -U --quiet pip setuptools wheel

echo "==> Installing Cyberzard (editable)"
REQ="$REPO_DIR"
if [ -n "$EXTRAS" ]; then REQ="$REQ[$EXTRAS]"; fi

# Try editable first; if it fails, fallback to non-editable
if ! "$VENV_DIR/bin/pip" install -e "$REQ"; then
  echo "==> Editable install failed; retrying non-editable"
  "$VENV_DIR/bin/pip" install "$REQ"
fi

echo "==> Linking CLI into $BIN_DIR"
if [ -f "$VENV_DIR/bin/cyberzard" ]; then
  ln -sf "$VENV_DIR/bin/cyberzard" "$BIN_DIR/cyberzard"
else
  echo "ERROR: cyberzard entrypoint not found in venv." >&2
  exit 1
fi

# PATH hint
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    SHELL_RC=""
    if [ -n "${BASH_VERSION:-}" ]; then SHELL_RC="$HOME/.bashrc"; fi
    if [ -n "${ZSH_VERSION:-}" ]; then SHELL_RC="$HOME/.zshrc"; fi
    echo ""
    echo "Add to PATH (one-time):"
    echo "  echo 'export PATH=\"$BIN_DIR:$PATH\"' >> ${SHELL_RC:-~/.profile} && source ${SHELL_RC:-~/.profile}"
    ;;
esac

echo ""
echo "✅ Cyberzard installed. Try: cyberzard scan"
