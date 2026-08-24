"""CLI entry point: fetch the RandomUser CSV and write it to the dbt seed directory."""

from randomuser_elt.client import get_randomuser_response
from randomuser_elt.write import seed_response_csv


def main() -> None:
    response = get_randomuser_response()
    seed_response_csv(response)


if __name__ == "__main__":
    main()
