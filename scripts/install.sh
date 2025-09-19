#!/usr/bin/env bash
set -euo pipefail

REPO="elwizard33/Cyberzard"
GH_API="https://api.github.com"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Detecting platform"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m | tr '[:upper:]' '[:lower:]')"
case "$ARCH" in
  x86_64|amd64) ARCH="x86_64" ;;
  arm64|aarch64) ARCH="arm64" ;;
esac
if [[ "$OS" == "darwin" ]]; then OS_TAG="macos"; else OS_TAG="linux"; fi
ASSET="cyberzard-${OS_TAG}-${ARCH}"

echo "==> Fetching latest release metadata"
JSON="$TMP_DIR/release.json"
curl -fsSL "${GH_API}/repos/${REPO}/releases/latest" -o "$JSON"

ASSET_URL=$(jq -r --arg NAME "$ASSET" '.assets[] | select(.name==$NAME) | .browser_download_url' "$JSON")
CHECKS_URL=$(jq -r '.assets[] | select(.name=="checksums.txt") | .browser_download_url' "$JSON")
TAG=$(jq -r '.tag_name' "$JSON")

if [[ -z "$ASSET_URL" || -z "$CHECKS_URL" || "$ASSET_URL" == "null" || "$CHECKS_URL" == "null" ]]; then
  echo "Error: Could not find assets for $ASSET" >&2
  exit 1
fi

echo "==> Downloading binary and checksums ($TAG)"
BIN="$TMP_DIR/$ASSET"
SUM="$TMP_DIR/checksums.txt"
curl -fsSL "$ASSET_URL" -o "$BIN"
curl -fsSL "$CHECKS_URL" -o "$SUM"

echo "==> Verifying checksum"
EXPECTED=$(grep -E "[[:xdigit:]]+\s+\*?$ASSET$" "$SUM" | awk '{print $1}')
if [[ -z "$EXPECTED" ]]; then
  echo "Error: checksum entry not found for $ASSET" >&2
  exit 1
fi
GOT=$(shasum -a 256 "$BIN" | awk '{print $1}')
if [[ "$EXPECTED" != "$GOT" ]]; then
  echo "Error: checksum mismatch. expected=$EXPECTED got=$GOT" >&2
  exit 1
fi

chmod +x "$BIN"

DEST_DIR="/usr/local/bin"
if [[ ! -w "$DEST_DIR" ]]; then
  if command -v sudo >/dev/null 2>&1; then
    echo "==> Installing to $DEST_DIR with sudo"
    sudo install -m 0755 "$BIN" "$DEST_DIR/cyberzard"
  else
    echo "==> No sudo; installing to ~/.local/bin"
    DEST_DIR="$HOME/.local/bin"
    mkdir -p "$DEST_DIR"
    install -m 0755 "$BIN" "$DEST_DIR/cyberzard"
    case ":$PATH:" in
      *":$DEST_DIR:"*) ;;
      *) echo "Add $DEST_DIR to your PATH" ;;
    esac
  fi
else
  echo "==> Installing to $DEST_DIR"
  install -m 0755 "$BIN" "$DEST_DIR/cyberzard"
fi

echo "==> Installed: $(command -v cyberzard || true)"
echo "==> Version: $(cyberzard version || true)"
echo "Done."
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
if [ -n "$EXTRAS" ]; then REQ="${REQ}[${EXTRAS}]"; fi

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
