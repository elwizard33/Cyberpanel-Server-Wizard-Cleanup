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

### Manual install (from source)
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .   # or .[openai] / .[anthropic]
```

### Install from release (pipx/pip)
Once official releases are published to PyPI:

```bash
pipx install cyberzard
# or with extras
pipx install 'cyberzard[openai]'

# Alternatively with pip
pip install cyberzard
```

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
```bash
git pull --rebase
pip install -e . --upgrade   # or non‑editable: pip install . --upgrade

From PyPI:
```bash
pipx upgrade cyberzard  # or: pip install -U cyberzard
```
```

## Troubleshooting

Editable install fails with message like:

> build backend is missing the 'build_editable' hook

Fix:
```bash
python -m pip install -U pip setuptools wheel
pip install -e .    # or non‑editable: pip install .
```
This commonly occurs on stock Ubuntu with older pip (22.x).

