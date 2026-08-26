"""Integration tests that hit the real RandomUser API.

Excluded from the default test run (see pyproject.toml addopts); run explicitly
with ``pytest -m integration``.
"""

import pytest

from randomuser_elt.client import get_randomuser_response
from randomuser_elt.config import ExtractSettings


@pytest.mark.integration
def test_get_randomuser_response_hits_live_api(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = ExtractSettings(
        _env_file=None,  # type: ignore[call-arg]
        source_url="https://randomuser.me/api/",
        source_format="csv",
        source_results=1,
        source_seed="integration-test",
        source_nat="gb",
        source_inc="gender,name,email",
    )
    monkeypatch.setattr("randomuser_elt.client.load_extract_settings", lambda: settings)

    response = get_randomuser_response()

    assert response.status_code == 200
    header = response.text.splitlines()[0]
    assert "email" in header
