"""Unit tests for randomuser_elt.write."""

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randomuser_elt.write import seed_response_csv


@pytest.fixture(autouse=True)
def _seed_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.chdir(tmp_path)
    seed_dir = tmp_path / "dbt" / "seeds"
    seed_dir.mkdir(parents=True)
    return seed_dir


def test_seed_response_csv_writes_response_text(tmp_path: Path) -> None:
    response = MagicMock(text="gender,email\nfemale,a@example.com\n")

    seed_response_csv(response)

    written = (tmp_path / "dbt" / "seeds" / "randomuser.csv").read_text()
    assert written == response.text


def test_seed_response_csv_logs_path_and_byte_count(
    caplog: pytest.LogCaptureFixture,
) -> None:
    response = MagicMock(text="gender,email\nfemale,a@example.com\n")

    with caplog.at_level(logging.INFO, logger="randomuser_elt.write"):
        seed_response_csv(response)

    assert any(
        "randomuser.csv" in record.message and str(len(response.text)) in record.message
        for record in caplog.records
    )
