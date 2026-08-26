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


def test_main_propagates_fetch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "randomuser_elt.__main__.get_randomuser_response",
        MagicMock(side_effect=ConnectionError("fetch failed")),
    )
    write_mock = MagicMock()
    monkeypatch.setattr("randomuser_elt.__main__.seed_response_csv", write_mock)

    with pytest.raises(ConnectionError, match="fetch failed"):
        main()

    write_mock.assert_not_called()


def test_main_propagates_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "randomuser_elt.__main__.get_randomuser_response", MagicMock(return_value="resp")
    )
    monkeypatch.setattr(
        "randomuser_elt.__main__.seed_response_csv",
        MagicMock(side_effect=PermissionError("write failed")),
    )

    with pytest.raises(PermissionError, match="write failed"):
        main()
