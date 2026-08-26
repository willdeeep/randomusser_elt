"""Unit tests for randomuser_elt.__main__."""

from unittest.mock import MagicMock

import pytest

from randomuser_elt.__main__ import main


def test_main_writes_the_fetched_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch_mock = MagicMock(return_value="the-response")
    write_mock = MagicMock()
    monkeypatch.setattr("randomuser_elt.__main__.get_randomuser_response", fetch_mock)
    monkeypatch.setattr("randomuser_elt.__main__.seed_response_csv", write_mock)

    main()

    write_mock.assert_called_once_with("the-response")


def test_main_configures_logging_before_running(monkeypatch: pytest.MonkeyPatch) -> None:
    basic_config_mock = MagicMock()
    monkeypatch.setattr("randomuser_elt.__main__.logging.basicConfig", basic_config_mock)
    monkeypatch.setattr(
        "randomuser_elt.__main__.get_randomuser_response", MagicMock(return_value="resp")
    )
    monkeypatch.setattr("randomuser_elt.__main__.seed_response_csv", MagicMock())

    main()

    basic_config_mock.assert_called_once()
