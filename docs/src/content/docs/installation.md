---
title: Installation
description: Install Cyberzard CLI and prerequisites
---

# Installation

## Prerequisites
- Python 3.10+ (3.11+ recommended)
- Git
- (Optional) LLM provider key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

## Install (Linux — one‑liner)
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

With AI extras (choose one):
```bash
CYBERZARD_EXTRAS=openai bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
# or
CYBERZARD_EXTRAS=anthropic bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

### Install from Release (no git)
We publish both Python wheels and standalone binaries for Linux and macOS (x86_64 and arm64).

Install the latest packaged wheel (Linux/macOS):
```bash
# Fetch the latest wheel's browser_download_url and install (no jq required)
WHEEL_URL=$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest \
	| grep -oE '"browser_download_url"\s*:\s*"[^"]+\.whl"' \
	| sed -E 's/.*"(https:[^"]+)"/\1/' | head -n1) && \
python3 -m pip install --user "$WHEEL_URL"
# Note: extras are supported when installing from an index (e.g. PyPI). For wheel files, install extras separately if needed.
```

Or download the file first (keeping its original name), then install:
```bash
WHEEL_URL=$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest \
	| grep -oE '"browser_download_url"\s*:\s*"[^"]+\.whl"' \
	| sed -E 's/.*"(https:[^"]+)"/\1/' | head -n1) && \
curl -fsSL -L -O -J "$WHEEL_URL" && \
python3 -m pip install --user "./$(basename "$WHEEL_URL")"
```

Fallback (derive the tag and construct the URL):
```bash
TAG=$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest \
	| sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[^"[:space:]]*\)".*/\1/p') && \
VER=${TAG#v} && \
python3 -m pip install --user \
	"https://github.com/elwizard33/Cyberzard/releases/download/${TAG}/cyberzard-${VER}-py3-none-any.whl"
```

Important: don’t rename the wheel file. Pip relies on the filename to parse version/metadata.

Alternatively, pin a specific versioned wheel:
```bash
python3 -m pip install --user \
	https://github.com/elwizard33/Cyberzard/releases/download/v0.1.3/cyberzard-0.1.3-py3-none-any.whl
```

### Manual install (from source)
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .   # or .[openai] / .[anthropic]
```

### Standalone binary (Linux)
On each GitHub Release we attach a Linux x86_64 binary:

- `cyberzard-linux-x86_64`

Download, `chmod +x`, and run on your Linux CyberPanel server:
```bash
curl -fsSL -o cyberzard-linux-x86_64 \
	https://github.com/elwizard33/Cyberzard/releases/download/$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[^"[:space:]]*\)".*/\1/p')/cyberzard-linux-x86_64 && \
chmod +x cyberzard-linux-x86_64
```

Verifying checksums:
```bash
curl -fsSL -O \
	https://github.com/elwizard33/Cyberzard/releases/download/$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[^"[:space:]]*\)".*/\1/p')/checksums.txt
shasum -a 256 cyberzard-* | grep -F -f <(cut -d' ' -f1 checksums.txt) || echo 'Checksum mismatch!'
```

Note: If you’re on macOS or Windows, deploy to or SSH into your Linux CyberPanel server and run the binary there. For local development on macOS, install from source.

### Install from release (PyPI)
Planned for future. For now, use the one-liner installer or source install above.

Run a basic command:
```bash
cyberzard scan
```

If you have a model key:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-... # or set via secret manager
cyberzard agent "Summarize current risks"
```

## Upgrade
From a git/installer-based install:
```bash
cyberzard --upgrade   # or: cyberzard upgrade
cyberzard upgrade --channel stable   # use latest tagged release
```

Manual (from source checkout):
```bash
git pull --rebase
pip install -e . --upgrade   # or pip install . --upgrade
```

When PyPI releases are available, this section will be updated.

See also: [Upgrade & Troubleshooting](./upgrade)

## Troubleshooting

Editable install fails with message like:

> build backend is missing the 'build_editable' hook

Fix:
```bash
python -m pip install -U pip setuptools wheel
pip install -e .    # or non‑editable: pip install .
```
This commonly occurs on stock Ubuntu with older pip (22.x).

Docs build on CI fails with rollup optional deps error:

> Cannot find module @rollup/rollup-linux-x64-gnu

Workaround (already applied in CI): remove node_modules and lockfile, then reinstall:
```bash
rm -rf docs/node_modules docs/package-lock.json
cd docs && npm install --legacy-peer-deps && npm run build
```

