"""RandomUser 1K CSV extraction client.

Responsible only for connecting to the source API: builds GET request URL, yields raw CSV.
Write to seeds lives elsewhere so this stays a thin I/O boundary.
"""

import requests
from tenacity import (
    Retrying,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from randomuser_elt.config import ExtractSettings, load_extract_settings

_NETWORK_ERRORS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
_RETRYABLE_STATUS_CODES = {429}  # plus any 5xx, checked separately below

_MAX_ATTEMPTS = 5
_TIMEOUT_SECONDS = 30.0
_BACKOFF_MIN_SECONDS = 1
_BACKOFF_MAX_SECONDS = 10


def _build_params(settings: ExtractSettings) -> dict[str, str]:
    raw: dict[str, str | int | list[str] | None] = {
        "format": settings.source_format,
        "results": settings.source_results,
        "seed": settings.source_seed,
        "nat": settings.source_nat,
        "inc": settings.source_inc,
    }
    return {
        key: ",".join(value) if isinstance(value, list) else str(value)
        for key, value in raw.items()
        if value is not None
    }


def _is_retryable_status(exception: BaseException) -> bool:
    response = getattr(exception, "response", None)
    if response is None:
        return False
    return response.status_code >= 500 or response.status_code in _RETRYABLE_STATUS_CODES


def _fetch(url: str, params: dict[str, str], timeout: float) -> requests.Response:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response


def get_randomuser_response() -> requests.Response:
    settings = load_extract_settings()
    params = _build_params(settings)

    should_retry = retry_if_exception_type(_NETWORK_ERRORS) | retry_if_exception(
        _is_retryable_status
    )
    retryer = Retrying(
        stop=stop_after_attempt(_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=_BACKOFF_MIN_SECONDS, max=_BACKOFF_MAX_SECONDS),
        retry=should_retry,
        reraise=True,
    )
    return retryer(_fetch, settings.source_url, params, _TIMEOUT_SECONDS)
