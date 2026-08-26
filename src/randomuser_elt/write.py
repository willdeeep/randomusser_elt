"""Write API response text to CSV

Write response text from client to CSV in dbt/seeds directory, raise exceptions as appropriate
"""

import logging

import requests

logger = logging.getLogger(__name__)

_SEED_PATH = "dbt/seeds/randomuser.csv"


def seed_response_csv(response: requests.Response) -> None:
    with open(_SEED_PATH, "w") as f:
        f.write(response.text)
    logger.info("Wrote %s (%d bytes)", _SEED_PATH, len(response.text))
