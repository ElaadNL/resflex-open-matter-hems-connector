"""Safe path helpers for OTA downloads."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from matter_server.common.errors import UpdateError


def safe_ota_download_path(base_dir: Path, url: str) -> Path:
    """Resolve an OTA download path that cannot escape ``base_dir``.

    Unquotes the URL path before taking the basename so encoded separators
    (for example ``%2F``) cannot turn the filename into an absolute path.
    """
    parsed_url = urlparse(url)
    # Decode first, then take basename — ordering matters for path traversal.
    file_name = Path(unquote(parsed_url.path)).name
    if (
        not file_name
        or file_name in {".", ".."}
        or "/" in file_name
        or "\\" in file_name
        or Path(file_name).is_absolute()
    ):
        raise UpdateError("Invalid OTA file name")

    base_dir = base_dir.resolve()
    file_path = (base_dir / file_name).resolve()
    if not file_path.is_relative_to(base_dir):
        raise UpdateError("Invalid OTA file name")
    return file_path


def safe_ota_local_path(base_dir: Path, url: str) -> Path:
    """Resolve a ``file://`` OTA path that must stay under ``base_dir``."""
    parsed_url = urlparse(url)
    # file:///absolute/path → path starts with /; strip leading slash for join.
    relative = unquote(parsed_url.path).lstrip("/")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise UpdateError("Invalid OTA file path")

    base_dir = base_dir.resolve()
    file_path = (base_dir / candidate).resolve()
    if not file_path.is_relative_to(base_dir):
        raise UpdateError("Invalid OTA file path")
    return file_path
