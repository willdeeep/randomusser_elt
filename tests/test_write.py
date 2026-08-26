"""Unit tests for randomuser_elt.write."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randomuser_elt.write import seed_response_csv


@pytest.fixture
def _seed_dir(isolate_test_environment: Path) -> Path:
    seed_dir = isolate_test_environment / "dbt" / "seeds"
    seed_dir.mkdir(parents=True)
    return seed_dir


def test_seed_response_csv_writes_response_text(_seed_dir: Path, tmp_path: Path) -> None:
    response = MagicMock(text="gender,email\nfemale,a@example.com\n")

    seed_response_csv(response)

    written = (tmp_path / "dbt" / "seeds" / "randomuser.csv").read_text()
    assert written == response.text


def test_seed_response_csv_logs_path_and_byte_count(
    _seed_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    response = MagicMock(text="gender,email\nfemale,a@example.com\n")

    with caplog.at_level(logging.INFO, logger="randomuser_elt.write"):
        seed_response_csv(response)

    assert any(
        "randomuser.csv" in record.message and str(len(response.text)) in record.message
        for record in caplog.records
    )


def test_seed_response_csv_raises_file_not_found_when_seed_dir_missing() -> None:
    """No _seed_dir fixture here -- dbt/seeds/ is never created."""
    response = MagicMock(text="gender,email\n")

    with pytest.raises(FileNotFoundError):
        seed_response_csv(response)


@pytest.mark.skipif(
    sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="directory write-permission bits aren't enforced the same way on Windows or as root",
)
def test_seed_response_csv_raises_permission_error_when_dir_not_writable(
    _seed_dir: Path,
) -> None:
    response = MagicMock(text="gender,email\n")
    _seed_dir.chmod(0o500)  # read + execute only, no write -- blocks file creation

    try:
        with pytest.raises(PermissionError):
            seed_response_csv(response)
    finally:
        _seed_dir.chmod(0o700)  # restore so pytest can clean up tmp_path
