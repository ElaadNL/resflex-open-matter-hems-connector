"""Tests for OTA path validation helpers."""

from pathlib import Path

import pytest

from matter_server.common.errors import UpdateError
from matter_server.server.ota.path_safety import (
    safe_ota_download_path,
    safe_ota_local_path,
)


def test_safe_ota_download_path_accepts_simple_filename(tmp_path: Path) -> None:
    """Normal OTA URLs resolve under the provider directory."""
    result = safe_ota_download_path(
        tmp_path, "https://example.com/fw/device-update.bin"
    )
    assert result == (tmp_path / "device-update.bin").resolve()


def test_safe_ota_download_path_encoded_absolute_stays_in_base(tmp_path: Path) -> None:
    """URL-encoded separators must not escape the download directory.

    Encoding the separator as ``%2F`` makes basename-then-unquote produce an
    absolute path; unquote-then-basename keeps the write inside ``base_dir``.
    """
    result = safe_ota_download_path(
        tmp_path,
        "https://example.com/fw/%2Fusr%2Flocal%2Fbin%2Fchip-ota-provider-app",
    )
    assert result == (tmp_path / "chip-ota-provider-app").resolve()
    assert result.is_relative_to(tmp_path.resolve())


def test_safe_ota_download_path_rejects_dotdot(tmp_path: Path) -> None:
    """Parent-directory segments in the basename are rejected."""
    with pytest.raises(UpdateError, match="Invalid OTA file name"):
        safe_ota_download_path(tmp_path, "https://example.com/fw/..")


def test_safe_ota_local_path_stays_under_base(tmp_path: Path) -> None:
    """Local file URLs must resolve under the OTA base directory."""
    nested = tmp_path / "images"
    nested.mkdir()
    target = nested / "update.bin"
    target.write_bytes(b"ota")
    result = safe_ota_local_path(tmp_path, f"file:///{nested.name}/update.bin")
    assert result == target.resolve()


def test_safe_ota_local_path_rejects_escape(tmp_path: Path) -> None:
    """Local file URLs must not escape the OTA base directory."""
    with pytest.raises(UpdateError, match="Invalid OTA file path"):
        safe_ota_local_path(tmp_path, "file:///../etc/passwd")
