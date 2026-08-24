# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffold: `pyproject.toml`, `.gitignore`, dbt seed
  directory, and the first working spike of the CSV extraction call.
- RandomUser extraction client (`src/randomuser_elt/client.py`) that builds a
  GET request to the randomuser.me API from configurable source params
  (format, results, seed, nationality, included fields) and returns the raw
  CSV response.
- Retry/backoff around the API call via `tenacity`: transient network errors,
  HTTP 429, and HTTP 5xx responses are retried with exponential backoff;
  HTTP 4xx client errors fail fast instead of being retried.
- `pydantic-settings` configuration (`src/randomuser_elt/config.py`):
  `ExtractSettings` loads source API params from `EXTRACT_`-prefixed
  environment variables, and `DbtSettings` loads dbt profile/project
  directories from `DBT_`-prefixed environment variables. Optional source
  params are omitted from the request entirely when unset, rather than being
  sent as empty/placeholder values.
- CSV seed writer (`src/randomuser_elt/write.py`) that writes the API
  response body to `dbt/seeds/randomuser.csv`.
- `.env.example` documenting the environment variables the project expects.
- Package build configuration (`[build-system]` / `[tool.hatch.build.targets.wheel]`
  in `pyproject.toml`) so `randomuser_elt` installs as an editable package via
  `uv sync`, matching the `randomuser_elt` console-script entry point.

### Changed

- Renamed the `src/extract` package to `src/randomuser_elt` to match the
  project name and the `[project.scripts]` entry point.
- Renamed `src/randomuser_elt/main.py` to `__main__.py` to match the
  `randomuser_elt.__main__:main` entry point declared in `pyproject.toml`.
