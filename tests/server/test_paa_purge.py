"""Tests for Chip-Test PAA purge helper."""

from pathlib import Path

from matter_server.server.helpers.paa_certificates import purge_chip_test_certificates


def test_purge_chip_test_certificates(tmp_path: Path) -> None:
    """Only Chip-Test development PAA files are removed."""
    keep = tmp_path / "dcld_production_example.pem"
    remove = tmp_path / "git_Chip-Test_abcd.pem"
    keep.write_text("keep")
    remove.write_text("remove")

    removed = purge_chip_test_certificates(tmp_path)

    assert removed == 1
    assert keep.exists()
    assert not remove.exists()
