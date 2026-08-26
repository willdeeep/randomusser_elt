"""Unit tests for randomuser_elt.client."""

import logging
from unittest.mock import MagicMock

import pytest
import requests

from randomuser_elt.client import _build_params, _is_retryable_status, get_randomuser_response
from randomuser_elt.config import ExtractSettings


def _settings(**overrides: object) -> ExtractSettings:
    defaults: dict[str, object] = {
        "source_url": "https://example.test/api/",
        "source_format": "csv",
        "source_results": 1000,
        "source_seed": "foobar",
        "source_nat": ["gb", "us"],
        "source_inc": ["gender", "email"],
    }
    defaults.update(overrides)
    return ExtractSettings(_env_file=None, **defaults)  # type: ignore[arg-type, call-arg]


def test_build_params_joins_list_values_with_commas() -> None:
    params = _build_params(_settings())

    assert params["nat"] == "gb,us"
    assert params["inc"] == "gender,email"


def test_build_params_omits_unset_optional_fields() -> None:
    params = _build_params(_settings(source_seed=None, source_nat=None))

    assert "seed" not in params
    assert "nat" not in params


def test_build_params_includes_required_fields() -> None:
    params = _build_params(_settings())

    assert params["format"] == "csv"
    assert params["results"] == "1000"


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_is_retryable_status_true_for_retryable_codes(status_code: int) -> None:
    response = MagicMock(status_code=status_code)
    exc = requests.exceptions.HTTPError(response=response)

    assert _is_retryable_status(exc) is True


def test_is_retryable_status_false_for_client_error() -> None:
    response = MagicMock(status_code=404)
    exc = requests.exceptions.HTTPError(response=response)

    assert _is_retryable_status(exc) is False


def test_is_retryable_status_false_when_exception_has_no_response() -> None:
    assert _is_retryable_status(ValueError("no response attribute")) is False


@pytest.fixture
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.sleep", lambda seconds: None)


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = MagicMock(status_code=status_code)
    return requests.exceptions.HTTPError(response=response)


def test_get_randomuser_response_returns_response_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    ok_response = MagicMock(status_code=200)
    ok_response.raise_for_status.return_value = None
    monkeypatch.setattr("randomuser_elt.client.requests.get", MagicMock(return_value=ok_response))

    result = get_randomuser_response()

    assert result is ok_response


def test_get_randomuser_response_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch, _no_real_sleep: None
) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    failing_response = MagicMock(status_code=500)
    failing_response.raise_for_status.side_effect = _http_error(500)
    ok_response = MagicMock(status_code=200)
    ok_response.raise_for_status.return_value = None

    mock_get = MagicMock(side_effect=[failing_response, ok_response])
    monkeypatch.setattr("randomuser_elt.client.requests.get", mock_get)

    result = get_randomuser_response()

    assert result is ok_response
    assert mock_get.call_count == 2


def test_get_randomuser_response_reraises_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch, _no_real_sleep: None
) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    failing_response = MagicMock(status_code=500)
    failing_response.raise_for_status.side_effect = _http_error(500)
    mock_get = MagicMock(return_value=failing_response)
    monkeypatch.setattr("randomuser_elt.client.requests.get", mock_get)

    with pytest.raises(requests.exceptions.HTTPError):
        get_randomuser_response()

    assert mock_get.call_count == 5


def test_get_randomuser_response_logs_request_params(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")
    ok_response = MagicMock(status_code=200)
    ok_response.raise_for_status.return_value = None
    monkeypatch.setattr("randomuser_elt.client.requests.get", MagicMock(return_value=ok_response))

    with caplog.at_level(logging.INFO, logger="randomuser_elt.client"):
        get_randomuser_response()

    assert any("https://example.test/api/" in record.message for record in caplog.records)


def test_get_randomuser_response_logs_warning_on_retry(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    _no_real_sleep: None,
) -> None:
    monkeypatch.setenv("EXTRACT_SOURCE_URL", "https://example.test/api/")

    failing_response = MagicMock(status_code=500)
    failing_response.raise_for_status.side_effect = _http_error(500)
    ok_response = MagicMock(status_code=200)
    ok_response.raise_for_status.return_value = None
    mock_get = MagicMock(side_effect=[failing_response, ok_response])
    monkeypatch.setattr("randomuser_elt.client.requests.get", mock_get)

    with caplog.at_level(logging.WARNING, logger="randomuser_elt.client"):
        get_randomuser_response()

    assert any(record.levelno == logging.WARNING for record in caplog.records)
