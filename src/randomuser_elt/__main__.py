"""CLI entry point: fetch the RandomUser CSV and write it to the dbt seed directory."""

import logging

from randomuser_elt.client import get_randomuser_response
from randomuser_elt.write import seed_response_csv


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    response = get_randomuser_response()
    seed_response_csv(response)


if __name__ == "__main__":
    main()
