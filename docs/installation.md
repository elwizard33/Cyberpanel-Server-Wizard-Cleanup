---
title: Installation
---
# Installation

This guide shows how to install, upgrade, and remove the CyberPanel AI Wizard CLI.

## 1. Requirements

Minimum:

- Python 3.10 or 3.11
- Linux (primary target) or macOS for development
- Network egress (only required if using AI providers)

Recommended for production scanning:

- Run inside a disposable analysis VM or container snapshot.
- Provide read access to target filesystem paths (some scans read cron, /etc, /var/www, /home).

## 2. Obtain the Source

Clone the repository (preferred for now until published on PyPI):

```bash
git clone https://github.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup.git
cd Cyberpanel-Server-Wizard-Cleanup
```

## 3. Create Virtual Environment (Optional but Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

## 4. Install (Editable / Developer Mode)

Editable install lets you pull updates without reinstalling:

```bash
pip install -e .
```

### 4.1 Install With AI Provider Extras

You can add one or both optional extras:

- OpenAI: `pip install -e .[openai]`
- Anthropic: `pip install -e .[anthropic]`
- Development + tests: `pip install -e .[dev]`

Multiple extras example:

```bash
pip install -e .[openai,anthropic,dev]
```

If extras fail due to shell globbing, quote the argument:

```bash
pip install '-e .[openai,anthropic]'
```

## 5. Quick Smoke Test

Run the CLI help:

```bash
cp-ai-wizard --help
```

Perform a dry scan (default is non-destructive):

```bash
cp-ai-wizard scan
```

JSON output example:

```bash
cp-ai-wizard scan --json | jq '.findings | length'
```

Run advice generation:

```bash
cp-ai-wizard advise
```

## 6. Configure AI Provider (Optional)

Set environment variables (See `configuration.md` for full list):

```bash
export OPENAI_API_KEY=sk-...        # for provider openai
export ANTHROPIC_API_KEY=...        # for provider anthropic
export CYBERZARD_MODEL_PROVIDER=openai
```

Then test an explanation:

```bash
cp-ai-wizard explain --provider openai --max-tokens 200
```

If keys are missing the tool silently degrades into non-AI mode.

## 7. Upgrading

Pull latest main (if installed editable):

```bash
git pull --rebase
pip install -e . --upgrade
```

If version pin changes add extras again:

```bash
pip install -e .[openai,anthropic] --upgrade
```

## 8. Uninstall

If installed editable, just remove the environment or directory:

```bash
deactivate || true
rm -rf .venv
```

If installed non-editable (future PyPI):

```bash
pip uninstall cyberpanel-ai-wizard
```

Remove evidence cache (optional):

```bash
sudo rm -rf /var/lib/cp-ai-wizard
```

## 9. Non-Root Usage

Most scans read system locations; run with sufficient privileges or provide bind-mounted paths inside a container.

## 10. Container / Ephemeral Usage (Planned)

Future docs will include a minimal container recipe. For now, prefer running directly on analysis host.

---

Next: Read `configuration.md` to customize runtime behavior.
