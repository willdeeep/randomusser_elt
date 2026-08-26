"""Unit tests for randomuser_elt.config.

These isolate from the project's real .env two ways: cwd is pointed at an
empty tmp_path (so ``env_file=".env"`` resolves to a file that doesn't exist),
and every EXTRACT_/DBT_ var is explicitly unset (so a value already present in
the real process environment -- e.g. from VSCode's ``python.envFile`` loading
.env into the test runner -- can't leak through unnoticed).
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from randomuser_elt.config import load_dbt_settings, load_extract_settings

_ENV_VARS = [
    "EXTRACT_SOURCE_URL",
    "EXTRACT_SOURCE_FORMAT",
    "EXTRACT_SOURCE_RESULTS",
    "EXTRACT_SOURCE_SEED",
    "EXTRACT_SOURCE_NAT",
    "EXTRACT_SOURCE_INC",
    "DBT_PROFILES_DIR",
    "DBT_PROJECT_DIR",
]


@pytest.fixture(autouse=True)
def _isolate_from_real_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_extract_settings_reads_prefixed_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    settings = load_extract_settings()

    assert settings.source_url == "https://example.test/api/"


def test_extract_settings_defaults_format_to_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    settings = load_extract_settings()

    assert settings.source_format == "csv"


def test_extract_settings_optional_fields_default_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    settings = load_extract_settings()

    assert settings.source_results is None
    assert settings.source_seed is None
    assert settings.source_nat is None
    assert settings.source_inc is None


def test_extract_settings_parses_json_list_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    monkeypatch.setenv("EXTRACT_SOURCE_NAT", '["gb","us"]')

    settings = load_extract_settings()

    assert settings.source_nat == ["gb", "us"]


def test_extract_settings_parses_plain_string_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    monkeypatch.setenv("EXTRACT_SOURCE_NAT", "gb")

    settings = load_extract_settings()

    assert settings.source_nat == "gb"


def test_extract_settings_missing_required_url_raises() -> None:
    with pytest.raises(ValidationError):
        load_extract_settings()


def test_dbt_settings_reads_prefixed_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DBT_PROFILES_DIR", "dbt")
    monkeypatch.setenv("DBT_PROJECT_DIR", "dbt")

    settings = load_dbt_settings()

    assert settings.profiles_dir == Path("dbt")
    assert settings.project_dir == Path("dbt")


def test_dbt_settings_missing_required_fields_raises() -> None:
    with pytest.raises(ValidationError):
        load_dbt_settings()
