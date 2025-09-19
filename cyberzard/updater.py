from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO = os.environ.get("CYBERZARD_GH_REPO", "elwizard33/Cyberzard")
GH_API = os.environ.get("CYBERZARD_GH_API", "https://api.github.com")
GH_DL = os.environ.get("CYBERZARD_GH_DL", "https://github.com")
GH_TOKEN = os.environ.get("CYBERZARD_GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
UA = os.environ.get("CYBERZARD_UA", "Cyberzard-Updater/1.0")
TIMEOUT = float(os.environ.get("CYBERZARD_HTTP_TIMEOUT", "20"))
RETRIES = int(os.environ.get("CYBERZARD_HTTP_RETRIES", "3"))
BACKOFF = float(os.environ.get("CYBERZARD_HTTP_BACKOFF", "1.5"))


@dataclass
class PlatformInfo:
    os_name: str
    arch: str
    asset_name: str


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")


def get_current_binary() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def detect_platform() -> PlatformInfo:
    sys_os = platform.system().lower()
    mach = platform.machine().lower()
    # Normalize arch
    if mach in {"x86_64", "amd64"}:
        arch = "x86_64"
    elif mach in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        arch = mach
    if sys_os.startswith("darwin") or sys_os == "mac" or sys_os == "macos":
        os_tag = "macos"
    elif sys_os.startswith("linux"):
        os_tag = "linux"
    else:
        os_tag = sys_os
    asset = f"cyberzard-{os_tag}-{arch}"
    return PlatformInfo(os_name=os_tag, arch=arch, asset_name=asset)


def _http_get(url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
    h = {"User-Agent": UA}
    # Prefer authenticated requests to avoid rate limits when token available
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    # Default to GitHub JSON accept if not overridden
    if not headers or "Accept" not in headers:
        h["Accept"] = "application/vnd.github+json"
    if headers:
        h.update(headers)
    last_err: Optional[Exception] = None
    for i in range(RETRIES):
        try:
            req = Request(url, headers=h)
            with urlopen(req, timeout=TIMEOUT) as resp:  # nosec - controlled url
                return resp.read()
        except (HTTPError, URLError, TimeoutError) as e:  # pragma: no cover - network
            last_err = e
            time.sleep(BACKOFF * (i + 1))
    if last_err:
        raise last_err
    raise RuntimeError("HTTP GET failed without exception")


def get_latest_release(repo: str = REPO, channel: str = "stable") -> dict:
    """Fetch release metadata.

    stable -> /releases/latest (excludes prereleases)
    edge   -> first item of /releases (may include prereleases, excludes drafts)
    """
    if channel == "edge":
        url = f"{GH_API}/repos/{repo}/releases?per_page=1"
        data = _http_get(url)
        items = json.loads(data.decode("utf-8"))
        # Pick the first non-draft release, allow prerelease
        if isinstance(items, list) and items:
            for it in items:
                if not it.get("draft"):
                    return it
        # Fallback to latest if list empty
    url = f"{GH_API}/repos/{repo}/releases/latest"
    data = _http_get(url)
    return json.loads(data.decode("utf-8"))


def select_asset(release: dict, asset_name: str) -> Tuple[Optional[dict], Optional[dict]]:
    assets = release.get("assets", [])
    target = None
    checksums = None
    for a in assets:
        name = a.get("name", "")
        if name == asset_name:
            target = a
        if name == "checksums.txt":
            checksums = a
    return target, checksums


def download_to(path: Path, url: str) -> None:
    data = _http_get(url, headers={"Accept": "application/octet-stream"})
    path.write_bytes(data)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_checksums(text: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # formats: "<sha>  <name>" or "<sha> *<name>"
        parts = line.split()
        if len(parts) >= 2:
            digest = parts[0]
            name = parts[-1].lstrip("*")
            mapping[name] = digest
    return mapping


def atomically_replace(current: Path, new_file: Path, backup_suffix: str = ".bak") -> None:
    backup = current.with_suffix(current.suffix + backup_suffix)
    try:
        if backup.exists():
            backup.unlink(missing_ok=True)
    except TypeError:
        # Python <3.8 compat just in case
        if backup.exists():
            backup.unlink()
    # Move current to backup, then move new into place
    tmp_dir = current.parent
    staged = tmp_dir / (current.name + ".staged")
    if staged.exists():
        staged.unlink()
    shutil.move(str(new_file), str(staged))
    shutil.move(str(current), str(backup))
    os.replace(staged, current)


def upgrade(repo: str = REPO, channel: str = "stable", dry_run: bool = False) -> Dict[str, str]:
    if not is_frozen():
        return {"status": "unsupported", "reason": "not_frozen"}
    current = get_current_binary()
    info = detect_platform()
    try:
        rel = get_latest_release(repo=repo, channel=channel)
    except HTTPError as e:  # pragma: no cover - network
        reason = "http_error"
        try:
            body = e.read().decode("utf-8") if hasattr(e, "read") else ""
            if "rate limit" in body.lower():
                reason = "rate_limited"
        except Exception:
            pass
        return {"status": "error", "reason": reason}
    except URLError:
        return {"status": "error", "reason": "network_error"}
    asset, checks = select_asset(rel, info.asset_name)
    if not asset:
        return {"status": "error", "reason": f"asset_not_found:{info.asset_name}"}
    if not checks:
        return {"status": "error", "reason": "checksums_missing"}
    asset_url = asset.get("browser_download_url") or asset.get("url")
    checks_url = checks.get("browser_download_url") or checks.get("url")
    if not (asset_url and checks_url):
        return {"status": "error", "reason": "asset_urls_missing"}
    # Resolve GitHub API asset URLs (need ? to redirect) if using API 'url'
    if asset_url.endswith("/assets") or "/assets/" in asset_url:
        asset_url = asset.get("browser_download_url", asset_url)
    if checks_url.endswith("/assets") or "/assets/" in checks_url:
        checks_url = checks.get("browser_download_url", checks_url)

    if dry_run:
        return {
            "status": "dry_run",
            "target": str(current),
            "asset": info.asset_name,
            "download": asset_url,
            "checksums": checks_url,
        }

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        bin_path = td_path / info.asset_name
        sum_path = td_path / "checksums.txt"
        download_to(sum_path, checks_url)
        checksums = parse_checksums(sum_path.read_text())
        expected = checksums.get(info.asset_name)
        if not expected:
            return {"status": "error", "reason": "checksum_entry_missing"}
        download_to(bin_path, asset_url)
        got = sha256(bin_path)
        if got.lower() != expected.lower():
            return {"status": "error", "reason": "checksum_mismatch", "expected": expected, "got": got}
        # Make executable
        bin_path.chmod(0o755)
        # Replace atomically
        atomically_replace(current, bin_path)
    return {"status": "ok", "target": str(current), "asset": info.asset_name, "version": rel.get("tag_name", "unknown")}
