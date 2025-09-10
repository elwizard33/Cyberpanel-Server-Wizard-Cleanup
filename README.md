<div align="center">

# 🛡️ Cyberzard & CyberPanel Cleanup

[![Docs](https://img.shields.io/badge/docs-Starlight%20Site-0b7285?logo=astro)](https://elwizard33.github.io/Cyberzard/)
[![Build Docs](https://github.com/elwizard33/Cyberzard/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/elwizard33/Cyberzard/actions/workflows/deploy-docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)
![Status](https://img.shields.io/badge/Status-Alpha-orange)
![AI Optional](https://img.shields.io/badge/AI-Optional-7c3aed)
![Offline‑first](https://img.shields.io/badge/Mode-Offline--first-495057)

</div>

Modern incident triage for CyberPanel:
- 🧰 Legacy bash cleanup scripts (basic & advanced)
- 🤖 Cyberzard — an AI‑assisted, safety‑constrained CLI for scanning, explaining, and planning remediation

---

## 🔗 Quick Links

- 📚 Docs: https://elwizard33.github.io/Cyberzard/
- 🧪 Try Cyberzard: see “Install & Use” below
- 🗺️ Roadmap: [ROADMAP.md](./ROADMAP.md)
- 🐞 Issues Guide: [ISSUE_GUIDE.md](./ISSUE_GUIDE.md)
- 📜 License: [MIT](./LICENSE)

---

<details>
<summary><strong>📖 Table of Contents</strong></summary>

- [Cyberzard — AI Security CLI](#-cyberzard--ai-security-cli)
  - [Features](#features)
  - [Install & Use](#install--use)
  - [Environment](#environment)
  - [Safety Model](#safety-model)
- [🧰 Legacy Cleanup Scripts](#-legacy-cleanup-scripts)
  - [Overview](#overview)
  - [Quick Start](#quick-start)
  - [Advanced vs Basic](#advanced-vs-basic)
  - [Decrypt Helpers](#decrypt-helpers)
- [🤝 Contributing](#-contributing)
- [⚠️ Disclaimer](#️-disclaimer)

</details>

---

## 🤖 Cyberzard — AI Security CLI

> Experimental preview. Interfaces may change until v0.1.

### Features

| Area | What you get |
|---|---|
| Multi‑source scanning | Files, processes, cron, services, users, SSH keys, encrypted files |
| Severity scoring | Critical/High/Medium/Low with rationale |
| Evidence preservation | Optional hashing/archiving prior to actions |
| Dry‑run planning | Generate remediation plan JSON first |
| AI reasoning (optional) | Summaries, prioritization, advice (OpenAI/Anthropic/none) |
| ReAct loop | Safe tool schema, sandboxed helpers |
| Output | Pretty tables + JSON |

### Install & Use

Fast install (Linux, user‑local, no sudo):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

With AI extras (choose one):

```bash
CYBERZARD_EXTRAS=openai bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
# or
CYBERZARD_EXTRAS=anthropic bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

Manual install (from source, editable):

```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .[openai]   # or .[anthropic] or just .
```

Note: No PyPI publishing yet. Use the installer or source install above. PyPI releases may be added later.

Common commands:

```bash
# Scan and pretty print
cyberzard scan

# JSON findings
cyberzard scan --json > findings.json

# Advice (static + optional AI enrichment)
CYBERZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=sk-... cyberzard advise

# Explain findings (AI)
OPENAI_API_KEY=sk-... cyberzard explain --provider openai

# Bounded reasoning loop (ReAct)
OPENAI_API_KEY=sk-... cyberzard agent "Top suspicious processes and rationale" --steps 4

# Remediation (requires explicit flags)
cyberzard remediate --delete --kill --preserve
```

Troubleshooting
- Editable install error (missing build_editable hook): upgrade pip/setuptools/wheel in a venv, or use non‑editable install:
  - `python -m pip install -U pip setuptools wheel`
  - `pip install .[openai]` (or `.[anthropic]` or just `.`)


### Environment

| Var | Purpose | Default |
|---|---|---|
| CYBERZARD_MODEL_PROVIDER | `openai`, `anthropic`, `none` | `none` |
| OPENAI_API_KEY | API key when provider=openai | — |
| ANTHROPIC_API_KEY | API key when provider=anthropic | — |
| CYBERZARD_EVIDENCE_DIR | Evidence dir | `/var/lib/cyberzard/evidence` |
| CYBERZARD_DRY_RUN | Global dry‑run | `true` |

### Safety Model

- No raw shell; curated, allow‑listed tools only
- Dry‑run by default; explicit flags to delete/kill
- Reasoning step cap; sandboxed helpers
- AI optional; offline works fine

---

## 🧰 Legacy Cleanup Scripts

### Overview

Basic and Advanced bash scripts to triage and clean common artifacts from the November CyberPanel attacks.

| Capability | Basic | Advanced |
|---|---|---|
| Diagnostics (files, processes, encrypted files) | ✅ | ✅ |
| Cleanup of artifacts | ✅ | ✅ |
| User + SSH key audit | — | ✅ |
| Interactive confirmations | — | ✅ |
| Extra post‑hardening tips | — | ✅ |

### Quick Start

Basic:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/wizard_cleanup.sh)"
```

Advanced:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/advanced_wizard_cleanup.sh)"
```

### Decrypt Helpers

- `.psaux` files: [1-decrypt.sh](https://gist.github.com/gboddin/d78823245b518edd54bfc2301c5f8882/raw/d947f181e3a1297506668e347cf0dec24b7e92d1/1-decrypt.sh)
- `.encryp` files: [encryp_dec.out](https://github.com/v0idxyz/babukencrypdecrytor/raw/c71b409cf35469bb3ee0ad593ad48c9465890959/encryp_dec.out)

---

## 🤝 Contributing

Please read the [Issue Guide](ISSUE_GUIDE.md) before filing.

- Small, focused PRs with tests/docs updates are welcome
- Clearly document environment and reproduction steps

## ⚠️ Disclaimer

These tools are provided as‑is, without warranty. Validate outputs before acting in production. Maintain backups and snapshots.

---

### Useful References

- [ManagingWP CyberPanel RCE Auth Bypass](https://github.com/managingwp/cyberpanel-rce-auth-bypass)
- [ArrayIterator's Cleanup Gist](https://gist.github.com/ArrayIterator/ebd67a0b4862e6bfb5d021c9f9d8dcd3)
- [Yoyosan's Cleanup Gist](https://gist.github.com/yoyosan/5f88c1a023f006f952d7378bdc7bcf01)
- [NothingCtrl's First Cleanup Gist](https://gist.github.com/NothingCtrl/710a12db2acb01baf66e3b4572919743)
- [NothingCtrl's Second Cleanup Gist](https://gist.github.com/NothingCtrl/78a7a8f0b2c35ada80bf6d52ac4cfef0)
- [Crosstyan's Cleanup Gist](https://gist.github.com/crosstyan/93966e4ab9c85b038e85308df1c8b420)

