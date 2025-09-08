---
title: Installation
---

# Installation

Clone and install locally (preview phase):
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python -m venv .venv && source .venv/bin/activate
pip install -e .[openai]  # or .[anthropic]
```

To update:
```bash
git pull
pip install -e . --upgrade
```

Troubleshooting: ensure Python >=3.10 and virtualenv isolation.
