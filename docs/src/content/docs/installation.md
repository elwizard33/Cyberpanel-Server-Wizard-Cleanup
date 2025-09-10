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
Install the latest packaged wheel from GitHub Releases (Linux/macOS):
```bash
# Get latest tag via GitHub API and install the matching wheel
TAG=$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest \
	| grep -oE '"tag_name"\s*:\s*"v[^"]+' | sed -E 's/.*"(v[^"]+)"/\1/') && \
python3 -m pip install --user \
	"https://github.com/elwizard33/Cyberzard/releases/download/${TAG}/cyberzard-${TAG#v}-py3-none-any.whl"
# Note: extras are supported when installing from an index (e.g. PyPI). For wheel files, install extras separately if needed.
```

Or download the file and keep its original filename, then install:
```bash
TAG=$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest \
	| grep -oE '"tag_name"\s*:\s*"v[^"]+' | sed -E 's/.*"(v[^"]+)"/\1/') && \
curl -fsSL -L -O -J \
	"https://github.com/elwizard33/Cyberzard/releases/download/${TAG}/cyberzard-${TAG#v}-py3-none-any.whl" && \
python3 -m pip install --user "./cyberzard-${TAG#v}-py3-none-any.whl"
```

Important: don’t rename the wheel file. Pip relies on the filename to parse version/metadata.

Alternatively, pin a specific versioned wheel:
```bash
python3 -m pip install --user \
	https://github.com/elwizard33/Cyberzard/releases/download/v0.1.2/cyberzard-0.1.2-py3-none-any.whl
```

### Manual install (from source)
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .   # or .[openai] / .[anthropic]
```

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

