"""Shared pytest fixtures for the randomuser_elt test suite."""

from pathlib import Path

import pytest

_OPTIONAL_VARS = [
    "EXTRACT_SOURCE_FORMAT",
    "EXTRACT_SOURCE_RESULTS",
    "EXTRACT_SOURCE_SEED",
    "EXTRACT_SOURCE_NAT",
    "EXTRACT_SOURCE_INC",
]

# Fields with no default in config.py -- a test that hits load_extract_settings()/
# load_dbt_settings() without setting these itself would otherwise get a
# ValidationError unrelated to whatever it's actually testing. A test that wants
# to exercise the missing-required-field case explicitly deletes one of these.
_REQUIRED_DEFAULTS = {
    "EXTRACT_SOURCE_URL": "https://example.test/api/",
    "DBT_PROFILES_DIR": "dbt",
    "DBT_PROJECT_DIR": "dbt",
}


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point cwd at an empty tmp_path, give every required field a safe default,
    and unset every optional EXTRACT_ var.

    Applies to every test in the suite so the real .env file and any ambient
    environment variable (e.g. loaded by an IDE's env-file setting) can never
    leak into a test, and so a test's pass/fail depends only on what confftest 
    and the test itself sets up.
    """
    monkeypatch.chdir(tmp_path)
    for var in _OPTIONAL_VARS:
        monkeypatch.delenv(var, raising=False)
    for var, default in _REQUIRED_DEFAULTS.items():
        monkeypatch.setenv(var, default)
    return tmp_path
