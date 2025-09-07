# CyberPanel Server Wizard Cleanup Scripts

[![Docs](https://img.shields.io/badge/docs-astro%20site-blue)](https://elwizard33.github.io/Cyberpanel-Server-Wizard-Cleanup/)

### Overview

These scripts are designed to help identify and clean potential malware and ransomware infections on CyberPanel servers. There are two versions available: the Basic version and the Advanced version. Both perform diagnostics to detect malicious files, suspicious processes, and encrypted files, followed by appropriate cleanup and decryption processes.

### Features of Both Scripts

- **Automated Diagnostics**: Identify malicious files, suspicious processes, and encrypted files.
- **Cleanup of Malicious Artifacts**: Remove detected malicious files and terminate suspicious processes.
- **Ransomware Decryption**: Attempt to decrypt files encrypted with known ransomware extensions.
- **Wizard-Themed Interface**: Engage users with an intuitive, themed experience guiding them through the cleanup process.

### Advanced Version Features

- **User Interaction**: Prompts users for confirmation before executing critical cleanup tasks, ensuring control over actions.
- **Detailed User and Key Auditing**: Scans for suspicious users and SSH keys, providing a detailed report of potential security threats.
- **Enhanced Security Recommendations**: Offers additional security measures to consider after cleanup.
- **Ensures Root Privileges**: Confirms the script is run with appropriate permissions for effective operation.

### Detailed Differences Between Versions

- **User Confirmation**: 
  - *Basic*: Executes tasks with minimal user input, focusing on efficiency.
  - *Advanced*: Interactively prompts the user for confirmations at critical steps to ensure actions align with user intent.
  
- **Malicious User and Key Checks**: 
  - *Basic*: Does not check for suspicious users or SSH keys.
  - *Advanced*: Includes comprehensive checks for unauthorized users and unexpected SSH keys, asking the user for validation.
  
- **Security Recommendations Post-Cleanup**:
  - *Basic*: Focuses on the immediate cleanup.
  - *Advanced*: Provides additional security tips post-cleanup, such as password changes and firewall adjustments.

### Decrypting Scripts

- **`.psaux` Files**: Decrypted using [1-decrypt.sh](https://gist.github.com/gboddin/d78823245b518edd54bfc2301c5f8882/raw/d947f181e3a1297506668e347cf0dec24b7e92d1/1-decrypt.sh).
- **`.encryp` Files**: Decrypted using [encryp_dec.out](https://github.com/v0idxyz/babukencrypdecrytor/raw/c71b409cf35469bb3ee0ad593ad48c9465890959/encryp_dec.out).

### Prerequisites

- Ensure you have `curl`, `wget`, and `bash` available on your system.
- **Take a Snapshot**: If you’re using a virtual machine, take a snapshot before you start to safeguard against unintended consequences.
- Follow cybersecurity best practices by backing up your data prior to running the scripts.

### Quick Start

You can directly download and execute the **Basic** version of the script using the following command:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup/refs/heads/main/scripts/wizard_cleanup.sh)"
```

For the **Advanced** version, use this command:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup/refs/heads/main/scripts/advanced_wizard_cleanup.sh)"
```

### Support

If you do not feel comfortable running these scripts or need further assistance, you can contact me at mago@elwizard.net for paid support.

### Acknowledgments

- Thank you to [@usmannasir](https://github.com/usmannasir) for sharing the decryption scripts used in this cleanup process.

### Other Tools For Cleaning The Attack

- [ManagingWP CyberPanel RCE Auth Bypass](https://github.com/managingwp/cyberpanel-rce-auth-bypass)
- [ArrayIterator's Cleanup Gist](https://gist.github.com/ArrayIterator/ebd67a0b4862e6bfb5d021c9f9d8dcd3)
- [Yoyosan's Cleanup Gist](https://gist.github.com/yoyosan/5f88c1a023f006f952d7378bdc7bcf01)
- [NothingCtrl's First Cleanup Gist](https://gist.github.com/NothingCtrl/710a12db2acb01baf66e3b4572919743)
- [NothingCtrl's Second Cleanup Gist](https://gist.github.com/NothingCtrl/78a7a8f0b2c35ada80bf6d52ac4cfef0)
- [Crosstyan's Cleanup Gist](https://gist.github.com/crosstyan/93966e4ab9c85b038e85308df1c8b420)

### Disclaimer

These scripts are provided as-is, without any warranty or guarantee. Use them at your own risk. The author is not responsible for any harm or loss resulting from the use of these scripts. Always ensure your environments are backed up and secure before running any security scripts.

---

# Cyberzard – AI Security CLI for CyberPanel

Cyberzard is the new name for the Python AI-assisted CyberPanel security CLI previously referenced here as the *CyberPanel AI Wizard*. It layers smart scanning, classification, natural‑language explanation, and guided remediation on top of (and beyond) the original bash cleanup scripts.

Current capabilities include modular scanners, severity scoring, remediation planning, evidence preservation hooks, AI provider abstraction (OpenAI / Anthropic / none), ReAct style agent with safe tool schema, advice enrichment, and rich / JSON reporting.

| Capability | Description |
|------------|-------------|
| Multi-source scanning | Replicates bash indicators (files, processes, cron, services, users, SSH keys, encrypted files) |
| Severity scoring | Normalizes findings into Critical/High/Medium/Low with rationale |
| Evidence preservation | Optional hashing & archiving before destructive actions |
| Dry-run & planning | Generate remediation plan JSON before executing |
| AI reasoning (optional) | Summaries, hardening advice, explanation of each finding |
| ReAct tool loop | Safe tool schema (read/list/search/scan/remediate plan) with sandboxed code execution |
| JSON + Rich TTY output | Machine-readable reports & human friendly tables |

## Early Development Status
Core functionality implemented (scanners, reporting, agent, advice enrichment). Packaging and hardening still in progress. Not yet published to PyPI.

## Install (local dev for now)
Clone repository and install editable with optional extras.

```bash
git clone https://github.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup.git
cd Cyberpanel-Server-Wizard-Cleanup
python -m venv .venv && source .venv/bin/activate
pip install -e .[openai]      # or .[anthropic]
```

Entry points: `cyberzard` (preferred) or `cp-ai-wizard` (legacy alias).

## Quick Usage

Scan and pretty print:
```bash
cyberzard scan
```

JSON findings (stable order):
```bash
cyberzard scan --json > findings.json
```

Generate advice (static + AI enrichment if provider configured):
```bash
AI_WIZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=sk-... cyberzard advise
```

Explain findings in natural language:
```bash
OPENAI_API_KEY=sk-... cyberzard explain --provider openai
```

Agent exploratory question (ReAct loop using safe tool schema):
```bash
OPENAI_API_KEY=sk-... cyberzard agent "List the most critical suspicious processes and rationale" --steps 4
```

Remediate (must explicitly allow destructive actions):
```bash
cyberzard remediate --delete --kill --preserve
```

Interactive shell:
```bash
cyberzard shell
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| AI_WIZARD_MODEL_PROVIDER | `openai`, `anthropic`, or `none` | `none` |
| OPENAI_API_KEY | OpenAI key (if provider=openai) | - |
| ANTHROPIC_API_KEY | Anthropic key (if provider=anthropic) | - |
| AI_WIZARD_EVIDENCE_DIR | Evidence / hashing directory | `/var/lib/cyberzard/evidence` |
| AI_WIZARD_DRY_RUN | Global dry-run toggle | `true` |
| AI_WIZARD_PRESERVE_EVIDENCE | Enable evidence preservation | `false` |
| AI_WIZARD_FORCE | Allow operations outside allowlist (danger) | `false` |
| AI_WIZARD_SEVERITY_FILTER | Minimum severity (info|low|medium|high|critical) | unset |
| AI_WIZARD_MAX_CONTEXT_BYTES | AI prompt truncation limit | `8000` |
| AI_WIZARD_NO_HISTORY | Disable agent step transcript retention | `false` |

If a provider is selected but its API key is missing, degraded (non-AI) mode is used automatically.

## Exit Codes (scan)
| Code | Meaning |
|------|---------|
| 0 | No findings or only info/low |
| 1 | Contains medium |
| 2 | Contains high |
| 3 | Contains critical |

## Current Commands

Auto-generated summary table (see full detailed reference in `docs/commands.md`). Regenerate with:

```bash
python scripts/generate_command_docs.py
```

| Command | Description |
|---------|-------------|
| scan | Run scanners and output findings (table or JSON) |
| advise | Show hardening tips (AI enrichment optional) |
| explain | Natural language summary of findings (AI) |
| agent | ReAct loop with tool calling for custom question |
| remediate | Apply limited remediation (explicit flags) |
| shell | Interactive minimal REPL |

## Safety Model
Destructive actions (file remove, process kill) remain dry-run unless corresponding flags are passed. Path deletions are constrained to an allowlist unless `AI_WIZARD_FORCE=true` is set. Sandboxed code execution tool performs AST validation and resource limiting. Missing provider credentials never block core scanning.

## Adding New Scanners
1. Create module in `ai_wizard/scanners/` subclassing `BaseScanner`.
2. Implement `scan()` returning `List[Finding]`.
3. Register in `SCANNER_REGISTRY` in `ai_wizard/scanners/__init__.py`.
4. Include rationale, recommended_action.

## Roadmap Updates
Planned next steps:
1. Automated unit tests for scanners & remediation executor.
2. Packaging polish & initial 0.1.0 release.
3. Extended composite correlation heuristics.
4. Persistent caching of previous scans for delta reporting.
5. Optional YARA integration for file classification.

## Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| "SDK not available" message | Provider not installed | Install extras: `pip install .[openai]` |
| Provider resets to none | Missing API key | Export correct key env var |
| No destructive actions happen | Dry-run still true | Pass `--delete/--kill` flags or set `AI_WIZARD_DRY_RUN=false` |
| Advice not enriched | AI disabled | Set provider + key |

## Contributing
PRs welcome once initial 0.1.0 is cut. Please keep modules cohesive and small, add/update tests for new scanners, and document any new environment variables.

## Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,openai]   # or .[dev,anthropic]
pytest -q
```

Optional lint (none configured yet) – suggestions:
* ruff for style/imports
* mypy for type checking

Run a local scan quickly:
```bash
cyberzard scan --json | jq '. | length'
```

Add a new scanner: follow steps in Adding New Scanners section and include at least one test asserting its output shape.

## Disclaimer
Prototype software. Validate outputs before acting on them in production. Always maintain off-host backups and snapshots.

## Security Design Highlights
- Path allowlist & force override requirement
- Evidence directory with hash + metadata
- Sandboxed execution: resource limits + AST validation (no imports / open / eval)
- No autonomous destructive actions without explicit user consent

## Roadmap (abridged)
1. Core scanners parity with bash (in progress)
2. Remediation planning + dry-run
3. Evidence preservation & hashing
4. AI explanation & advice enrichment
5. Sandboxed code execution tools
6. Packaging release 0.1.0

---

