---
title: Installation
description: Install Cyberzard CLI and prerequisites
---

# Installation

## Prerequisites
- Python 3.11+
- Git
- (Optional) LLM provider key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

## Install
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
pip install -e .
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
pip install -e . --upgrade
```

