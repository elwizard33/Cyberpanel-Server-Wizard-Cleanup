from __future__ import annotations
"""n8n setup assistant module (skeleton).

This module will provide the implementation for the `cyberzard n8n-setup` command.
It will support interactive (Rich styled) and non-interactive generation of scripts
and optional application of deployment steps for n8n on CyberPanel.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List
import sys
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import importlib
import json

try:  # Rich is an existing dependency used elsewhere (ui.py, chat.py)
    from rich.console import Console  # type: ignore
except Exception:  # pragma: no cover - fallback if Rich unavailable
    Console = None  # type: ignore


@dataclass
class N8nSetupConfig:
    """Configuration holder for upcoming n8n setup implementation (placeholder)."""
    mode: Optional[str] = None
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    port: int = 5678


def _is_tty() -> bool:
    """Return True if output is an interactive TTY and NO_COLOR not set."""
    return bool(sys.stdout.isatty() and os.getenv("NO_COLOR") not in {"1", "true", "TRUE"})


def _console():  # pragma: no cover - trivial
    """Return a Rich Console if available & TTY, else None."""
    if Console and _is_tty():  # type: ignore
        try:
            return Console()  # type: ignore
        except Exception:
            return None
    return None


def run_n8n_setup(**kwargs: Any) -> Dict[str, Any]:
    """Programmatic orchestration for n8n setup.

    Kwargs may include: domain, subdomain, mode, port, basic_auth, basic_auth_user,
    timezone, n8n_image, postgres_image, write_only, out_dir, overwrite, json_out.
    Returns a dict summary for callers; prints Rich-styled messages when TTY.
    """
    cons = _console()
    provided = dict(kwargs)
    interactive = bool(kwargs.get("interactive", False))
    prefs, warns, errs = collect_preferences(interactive=interactive, provided=provided)
    w2, e2 = validate_environment(prefs)
    warns += w2
    errs += e2
    if errs:
        if cons:
            cons.print("[red]Errors:[/red]\n" + "\n".join(f" - {e}" for e in errs))
        return {"ok": False, "errors": errs, "warnings": warns}
    if warns and cons:
        cons.print("[yellow]Warnings:[/yellow]\n" + "\n".join(f" - {w}" for w in warns))

    mode_val = prefs["mode"] or "native"
    setup_script = generate_native_script(prefs) if mode_val == "native" else generate_tunnel_script(prefs)
    update_script = generate_update_script_native(prefs) if mode_val == "native" else generate_update_script_tunnel(prefs)

    write_only = bool(kwargs.get("write_only", False))
    out_dir = kwargs.get("out_dir")
    overwrite = bool(kwargs.get("overwrite", False))
    json_out = bool(kwargs.get("json_out", False))
    paths: List[str] = []
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        setup_path = os.path.join(out_dir, f"n8n_setup_{mode_val}.sh")
        update_path = os.path.join(out_dir, f"n8n_update_{mode_val}.sh")
        paths.append(write_script(setup_path, setup_script, overwrite=overwrite))
        paths.append(write_script(update_path, update_script, overwrite=overwrite))
        if cons:
            cons.print("[green]Wrote scripts:[/green]\n" + "\n".join(f" - {p}" for p in paths))

    ok = True
    applied = False
    apply_path = None
    if not write_only:
        if mode_val == "native":
            ok, apply_path = apply_native(prefs, save_to=(paths[0] if paths else None), overwrite=overwrite)
        else:
            ok, apply_path = apply_tunnel(prefs, save_to=(paths[0] if paths else None), overwrite=overwrite)
        applied = ok
        if cons:
            if ok:
                cons.print(f"[bold green]Applied {mode_val} setup[/bold green]: {apply_path}")
            else:
                cons.print(f"[red]Apply failed[/red]: {apply_path}")

    summary = {
        "ok": bool(ok),
        "applied": applied,
        "mode": mode_val,
        "prefs": sanitize_prefs_for_json(prefs),
        "scripts": paths,
        "apply_script": apply_path,
        "warnings": warns,
    }
    if json_out and not cons:
        print(json.dumps(summary))
    return summary


__all__ = ["run_n8n_setup", "N8nSetupConfig"]


# -------------------------------
# Preference Collection & Validation
# -------------------------------

DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
SUBDOMAIN_RE = re.compile(r"^[A-Za-z0-9-]{1,63}$")


def collect_preferences(interactive: bool, provided: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Collect and validate raw preference inputs (interactive or non-interactive).

    Returns (prefs, warnings, errors).
    Only minimal prompting logic added here (full styling/flow comes later).
    """
    prefs: Dict[str, Any] = {}
    warnings: List[str] = []
    errors: List[str] = []

    # Defaults
    defaults = {
        "mode": None,
        "domain": None,
        "subdomain": "n8n",
        "port": 5678,
        "timezone": "UTC",
        "basic_auth": False,
        "basic_auth_user": "admin",
        "basic_auth_pass": None,
        "resource_cpus": None,
        "resource_memory": None,
        "n8n_image": "n8nio/n8n:latest",
        "postgres_image": "postgres:16",
        "cloudflared_url": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
        "create_user": True,
        "user_name": "n8nuser",
    }
    # Merge provided
    for k, v in defaults.items():
        prefs[k] = provided.get(k, v)

    # Interactive prompts (minimal for skeleton stage)
    if interactive:
        try:
            typer = importlib.import_module("typer")  # type: ignore
        except Exception:  # pragma: no cover
            typer = None  # type: ignore
        if prefs["mode"] is None and typer:
            prefs["mode"] = typer.prompt("Choose mode (native|tunnel)", default="native").strip()
        if prefs["domain"] is None and typer:
            prefs["domain"] = typer.prompt("Root domain (example.com)").strip()

    # Basic validation
    mode = (prefs.get("mode") or "").strip().lower()
    if mode and mode not in {"native", "tunnel"}:
        errors.append("Invalid mode (expected 'native' or 'tunnel')")
    prefs["mode"] = mode or None

    domain = prefs.get("domain")
    if domain:
        if not DOMAIN_RE.match(domain):
            errors.append("Invalid domain format")
    else:
        errors.append("Domain is required (provide --domain)")

    sub = prefs.get("subdomain")
    if sub and not SUBDOMAIN_RE.match(sub):
        errors.append("Invalid subdomain (allowed: letters, digits, hyphen)")

    try:
        port_val = int(prefs.get("port", 5678))
        if not (1024 <= port_val <= 65535):
            errors.append("Port must be between 1024 and 65535")
        prefs["port"] = port_val
    except Exception:
        errors.append("Port must be an integer")

    # Secrets generation
    if prefs.get("basic_auth") and not prefs.get("basic_auth_pass"):
        prefs["basic_auth_pass"] = secrets.token_urlsafe(32)
    # DB password always generated (stored under db_password)
    prefs["db_password"] = secrets.token_urlsafe(32)

    return prefs, warnings, errors


def validate_environment(prefs: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Check host environment prerequisites. Returns (warnings, errors)."""
    warnings: List[str] = []
    errors: List[str] = []

    if not shutil.which("docker"):
        warnings.append("docker not found in PATH (apply mode will fail)")
    if prefs.get("mode") == "tunnel" and not shutil.which("cloudflared"):
        warnings.append("cloudflared not found (will attempt install in tunnel mode)")
    if prefs.get("create_user") and os.geteuid() != 0:
        warnings.append("Not root: user creation will be skipped")
        prefs["create_user"] = False
    return warnings, errors


# Extend export list
__all__.extend(["collect_preferences", "validate_environment"])


# -------------------------------
# Script Generation
# -------------------------------

def _header_comment(prefs: Dict[str, Any]) -> str:
        return (
                "# Generated by cyberzard n8n-setup\n"
                "# Mode: {mode}\n".format(mode=prefs.get("mode")) +
                "# Domain: {sd}.{d}\n".format(sd=prefs.get("subdomain"), d=prefs.get("domain")) +
                "# Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')\n"
                "# Edit carefully; re-run generator for changes.\n"
        )


def generate_native_script(prefs: Dict[str, Any]) -> str:
    """Build native (OpenLiteSpeed reverse proxy) deployment bash script."""
    domain = prefs["domain"]
    sub = prefs["subdomain"]
    port = prefs["port"]
    db_pass = prefs["db_password"]
    n8n_img = prefs["n8n_image"]
    pg_img = prefs["postgres_image"]
    tz = prefs.get("timezone", "UTC")
    cpus = prefs.get("resource_cpus")
    mem = prefs.get("resource_memory")
    basic = prefs.get("basic_auth")
    basic_user = prefs.get("basic_auth_user")
    basic_pass = prefs.get("basic_auth_pass")

    limits = []
    if cpus:
        limits.append(f"--cpus={cpus}")
    if mem:
        limits.append(f"--memory={mem}")
    limits_str = " ".join(limits)

    basic_env = ""
    if basic:
        basic_env = (
            "  -e N8N_BASIC_AUTH_ACTIVE=true \\\n"
            f"  -e N8N_BASIC_AUTH_USER={basic_user} \\\n"
            f"  -e N8N_BASIC_AUTH_PASSWORD={basic_pass} \\\n"
        )

    script = f"""#!/usr/bin/env bash
set -euo pipefail
{_header_comment(prefs)}

DOMAIN="{domain}"
SUBDOMAIN="{sub}"
N8N_PORT={port}
DB_PASS='{db_pass}'
N8N_DIR="$HOME/n8n-data"
POSTGRES_DIR="$HOME/postgres-data"
NETWORK="n8n-net"

mkdir -p "$N8N_DIR" "$POSTGRES_DIR"
docker network create "$NETWORK" >/dev/null 2>&1 || true

echo "[+] Starting PostgreSQL container"
docker run -d \
    --name n8n-postgres \
    --network "$NETWORK" \
    -e POSTGRES_USER=n8n \
    -e POSTGRES_PASSWORD=$DB_PASS \
    -e POSTGRES_DB=n8n \
    -v "$POSTGRES_DIR:/var/lib/postgresql/data" \
    {pg_img}

echo "[+] Starting n8n container"
docker run -d \
    --name n8n \
    --network "$NETWORK" \
    -p 127.0.0.1:$N8N_PORT:5678 \
    -v "$N8N_DIR:/home/node/.n8n" \
    -e DB_TYPE=postgresdb \
    -e DB_POSTGRESDB_HOST=n8n-postgres \
    -e DB_POSTGRESDB_PORT=5432 \
    -e DB_POSTGRESDB_DATABASE=n8n \
    -e DB_POSTGRESDB_USER=n8n \
    -e DB_POSTGRESDB_PASSWORD=$DB_PASS \
    -e N8N_HOST=$SUBDOMAIN.$DOMAIN \
    -e N8N_PORT=5678 \
    -e N8N_PROTOCOL=https \
    -e WEBHOOK_URL=https://$SUBDOMAIN.$DOMAIN/ \
    -e NODE_ENV=production \
    -e GENERIC_TIMEZONE={tz} \\
{basic_env}  {limits_str} \
    {n8n_img}

echo "[+] Ensure OpenLiteSpeed reverse proxy configuration present (manual append if needed)"
echo "[i] Issue SSL via CyberPanel CLI"
cyberpanel issueSSL --domain "$SUBDOMAIN.$DOMAIN" || true
echo "[i] Restarting OpenLiteSpeed"
sh /usr/local/lsws/bin/lswsctrl restart || true

echo "[✓] n8n native setup complete: https://$SUBDOMAIN.$DOMAIN (store DB_PASS securely)"
"""
    return script


def generate_tunnel_script(prefs: Dict[str, Any]) -> str:
        """Build docker compose + cloudflared tunnel deployment script."""
        domain = prefs["domain"]
        sub = prefs["subdomain"]
        port = prefs["port"]
        db_pass = prefs["db_password"]
        n8n_img = prefs["n8n_image"]
        pg_img = prefs["postgres_image"]
        tz = prefs.get("timezone", "UTC")
        basic = prefs.get("basic_auth")
        basic_user = prefs.get("basic_auth_user")
        basic_pass = prefs.get("basic_auth_pass")
        cloudflared_url = prefs.get("cloudflared_url")

        basic_yaml = ""
        if basic:
                basic_yaml = (
                        "      - N8N_BASIC_AUTH_ACTIVE=true\n"
                        f"      - N8N_BASIC_AUTH_USER={basic_user}\n"
                        f"      - N8N_BASIC_AUTH_PASSWORD={basic_pass}\n"
                )

        compose_yaml = f"""version: '3.8'
services:
    postgres:
        image: {pg_img}
        restart: always
        environment:
            POSTGRES_USER: n8n
            POSTGRES_PASSWORD: {db_pass}
            POSTGRES_DB: n8n
        volumes:
            - postgres_data:/var/lib/postgresql/data
        networks:
            - n8n-net

    n8n:
        image: {n8n_img}
        restart: always
        ports:
            - "127.0.0.1:{port}:5678"
        environment:
            - DB_TYPE=postgresdb
            - DB_POSTGRESDB_HOST=postgres
            - DB_POSTGRESDB_PORT=5432
            - DB_POSTGRESDB_DATABASE=n8n
            - DB_POSTGRESDB_USER=n8n
            - DB_POSTGRESDB_PASSWORD={db_pass}
            - N8N_HOST={sub}.{domain}
            - N8N_PORT=5678
            - N8N_PROTOCOL=https
            - WEBHOOK_URL=https://{sub}.{domain}/
            - NODE_ENV=production
            - GENERIC_TIMEZONE={tz}
            - N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
{basic_yaml}    volumes:
            - n8n_data:/home/node/.n8n
            - ./local-files:/files
        depends_on:
            - postgres
        networks:
            - n8n-net

volumes:
    postgres_data:
    n8n_data:

networks:
    n8n-net:
"""

        script = f"""#!/usr/bin/env bash
set -euo pipefail
{_header_comment(prefs)}

DOMAIN="{domain}"
SUBDOMAIN="{sub}"
N8N_PORT={port}
DB_PASS='{db_pass}'
PROJECT_DIR="$HOME/n8n-stack"
TUNNEL_NAME="n8n-tunnel"

mkdir -p "$PROJECT_DIR/local-files"
cd "$PROJECT_DIR"

echo "[+] Downloading cloudflared package"
curl -L {cloudflared_url} -o cloudflared.deb
sudo dpkg -i cloudflared.deb || true
rm -f cloudflared.deb

echo "[!] Run 'cloudflared tunnel login' in another terminal if not already authenticated"
cloudflared tunnel login || true

echo "[+] Creating tunnel"
cloudflared tunnel create $TUNNEL_NAME || true
TUNNEL_UUID=$(cloudflared tunnel list | awk '/n8n-tunnel/ {{print $1; exit}}')
echo "Tunnel UUID: $TUNNEL_UUID"

echo "[+] Routing DNS"
cloudflared tunnel route dns "$TUNNEL_UUID" "$SUBDOMAIN.$DOMAIN" || true

echo "[+] Writing cloudflared config"
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: $TUNNEL_UUID
credentials-file: ~/.cloudflared/$TUNNEL_UUID.json
ingress:
  - hostname: $SUBDOMAIN.$DOMAIN
    service: http://localhost:$N8N_PORT
  - service: http_status:404
EOF

echo "[+] Starting cloudflared service"
cloudflared service install || true
sudo systemctl enable cloudflared || true
sudo systemctl start cloudflared || true

echo "[+] Writing docker-compose.yml"
cat > docker-compose.yml <<'YAML'
{compose_yaml}YAML

docker compose up -d

echo "[✓] n8n tunnel setup complete: https://$SUBDOMAIN.$DOMAIN (store DB_PASS securely)"
"""
        return script


def generate_update_script_native(prefs: Dict[str, Any]) -> str:
        return f"""#!/usr/bin/env bash
set -euo pipefail
# Update script for native n8n deployment
docker pull {prefs['n8n_image']}
docker pull {prefs['postgres_image']}
docker rm -f n8n || true
docker rm -f n8n-postgres || true
echo "Re-run original setup script to recreate containers (data preserved in volumes)"
"""


def generate_update_script_tunnel(prefs: Dict[str, Any]) -> str:
        return f"""#!/usr/bin/env bash
set -euo pipefail
# Update script for tunnel (compose) n8n deployment
cd "$HOME/n8n-stack"
docker compose pull
docker compose up -d --force-recreate n8n
echo "Updated n8n container (DB persisted)."
"""

__all__.extend([
        "generate_native_script",
        "generate_tunnel_script",
        "generate_update_script_native",
        "generate_update_script_tunnel",
])


# -------------------------------
# Script Write & Sanitization Utilities
# -------------------------------

def write_script(path: str, content: str, overwrite: bool = False) -> str:
    """Write script content to path with 0750 perms. Returns path.

    Raises ValueError if file exists and overwrite is False.
    """
    p = os.path.abspath(path)
    if os.path.exists(p) and not overwrite:
        raise ValueError(f"Refusing to overwrite existing file: {p}")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)
    try:
        os.chmod(p, 0o750)
    except Exception:
        pass
    return p


REDACT_KEYS = {"basic_auth_pass", "db_password"}


def sanitize_prefs_for_json(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Return shallow copy of prefs with sensitive fields redacted."""
    out = dict(prefs)
    for k in REDACT_KEYS:
        if k in out and out[k]:
            out[k] = "***redacted***"
    return out


__all__.extend(["write_script", "sanitize_prefs_for_json"])


# -------------------------------
# Apply Execution Helpers
# -------------------------------

def _write_and_run_script(content: str) -> Tuple[bool, str]:
    """Write content to a temp file and execute with bash. Returns (ok, path)."""
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, prefix="cz-n8n-", suffix=".sh", encoding="utf-8") as tf:
            tf.write(content)
            tmp_path = tf.name
        try:
            os.chmod(tmp_path, 0o750)
        except Exception:
            pass
        proc = subprocess.run(["/bin/bash", tmp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ok = proc.returncode == 0
        return ok, tmp_path
    except Exception:
        return False, ""


def apply_native(prefs: Dict[str, Any], *, save_to: Optional[str] = None, overwrite: bool = False) -> Tuple[bool, str]:
    """Generate and apply native setup. Returns (success, script_path or reason)."""
    if not shutil.which("docker"):
        return False, "docker not found"
    script = generate_native_script(prefs)
    if save_to:
        try:
            path = write_script(save_to, script, overwrite=overwrite)
        except Exception as e:
            return False, f"write failed: {e}"
        ok, _ = _write_and_run_script(script)
        return ok, path
    ok, path = _write_and_run_script(script)
    return ok, path


def apply_tunnel(prefs: Dict[str, Any], *, save_to: Optional[str] = None, overwrite: bool = False) -> Tuple[bool, str]:
    """Generate and apply tunnel setup. Returns (success, script_path or reason)."""
    if not shutil.which("docker"):
        return False, "docker not found"
    # cloudflared is optional (script attempts to install), so we don't hard-fail here
    script = generate_tunnel_script(prefs)
    if save_to:
        try:
            path = write_script(save_to, script, overwrite=overwrite)
        except Exception as e:
            return False, f"write failed: {e}"
        ok, _ = _write_and_run_script(script)
        return ok, path
    ok, path = _write_and_run_script(script)
    return ok, path


__all__.extend(["apply_native", "apply_tunnel"])
