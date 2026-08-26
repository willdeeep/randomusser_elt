"""Unit tests for randomuser_elt.config.

Isolation from the project's real .env (cwd + env vars) is provided by the
autouse ``isolate_test_environment`` fixture in tests/conftest.py.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from randomuser_elt.config import load_dbt_settings, load_extract_settings


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


def test_extract_settings_parses_results_as_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    monkeypatch.setenv("EXTRACT_SOURCE_RESULTS", "1000")

    settings = load_extract_settings()

    assert settings.source_results == 1000


def test_extract_settings_parses_inc_json_list_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    monkeypatch.setenv("EXTRACT_SOURCE_INC", '["gender","email"]')

    settings = load_extract_settings()

    assert settings.source_inc == ["gender", "email"]


def test_extract_settings_parses_inc_plain_string_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    monkeypatch.setenv("EXTRACT_SOURCE_INC", "gender")

    settings = load_extract_settings()

    assert settings.source_inc == "gender"


def test_extract_settings_missing_required_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXTRACT_SOURCE_URL", raising=False)

    with pytest.raises(ValidationError):
        load_extract_settings()


def test_dbt_settings_reads_prefixed_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DBT_PROFILES_DIR", "dbt")
    monkeypatch.setenv("DBT_PROJECT_DIR", "dbt")

    settings = load_dbt_settings()

    assert settings.profiles_dir == Path("dbt")
    assert settings.project_dir == Path("dbt")


def test_dbt_settings_missing_required_fields_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBT_PROFILES_DIR", raising=False)
    monkeypatch.delenv("DBT_PROJECT_DIR", raising=False)

    with pytest.raises(ValidationError):
        load_dbt_settings()
