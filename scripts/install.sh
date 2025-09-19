#!/usr/bin/env bash
# Cyberzard Linux installer (single-line)
# Usage:
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
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
  *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;;
esac
if [[ "$OS" != "linux" ]]; then
  echo "This installer currently supports Linux only." >&2
  exit 1
fi
ASSET="cyberzard-linux-$ARCH"

echo "==> Fetching latest release metadata"
REL="$TMP_DIR/release.json"
curl -fsSL "${GH_API}/repos/${REPO}/releases/latest" -o "$REL"

asset_url() {
  awk -v name="$1" '
    $0 ~ /"assets"/ { in_assets=1 }
    in_assets && $0 ~ /"browser_download_url"/ { url=$0 }
    in_assets && $0 ~ /"name"/ {
      if ($0 ~ name) {
        gsub(/.*"browser_download_url": "|",?$/, "", url);
        print url; exit
      }
    }
  ' "$REL"
}

ASSET_URL=$(asset_url "$ASSET")
CHECKS_URL=$(asset_url "checksums.txt")
if [[ -z "${ASSET_URL:-}" || -z "${CHECKS_URL:-}" ]]; then
  echo "Error: release assets not found (asset=$ASSET)" >&2
  exit 1
fi

echo "==> Downloading binary and checksums"
BIN="$TMP_DIR/$ASSET"
SUM="$TMP_DIR/checksums.txt"
curl -fsSL "$ASSET_URL" -o "$BIN"
curl -fsSL "$CHECKS_URL" -o "$SUM"

echo "==> Verifying checksum"
EXPECTED=$(grep -E "^[0-9a-fA-F]{64}\s+\*?$ASSET$" "$SUM" | awk '{print $1}')
if [[ -z "${EXPECTED:-}" ]]; then
  echo "Error: checksum entry missing for $ASSET" >&2
  exit 1
fi
GOT=$(sha256sum "$BIN" | awk '{print $1}')
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
