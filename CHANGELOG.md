# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-27

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
- `dbt` project scaffold (`dbt_project.yml`, `profiles.yml` for the SQLite
  adapter, `packages.yml` declaring `dbt_utils`) and a `_seeds.yml` schema
  for the raw seed load.
- Staging layer: `stg_randomuser` typing and renaming every column from the
  raw seed (e.g. `name.first` -> `first_name`), fully documented and tested
  in `_staging.yml`.
- Core layer: `dim_user`, `dim_location`, `dim_timezone` — a pragmatic,
  non-3NF normalization that splits only on the one real functional
  dependency in the data (`timezone.offset -> timezone.description`) and the
  person/address boundary. Deterministic surrogate keys are generated via
  `row_number()` over a stable natural key, zero-padded, since SQLite has no
  native `md5()` and this project deliberately avoids adding a compiled
  crypto extension just to get one.
- `age_in_years` macro (`dbt/macros/age_in_years.sql`): whole years between
  now and a `dob` column, shared by the marts `age` column and a
  `dbt_utils.expression_is_true` drift-check test (severity `warn`) that
  compares it against the seed's static `dob_age`.
- Marts layer: `mart_recent_registrations_by_state` — the 3 most recently
  registered users per US state, via `row_number()` partitioned by state and
  filtered to `country = 'United States'` before ranking.
- `tasks.py`: a centralized `invoke` task layer (`extract`, `parse`, `debug`,
  `deps`, `seed`, `clean`, `build`, `reset-db`, `results`) wrapping every
  `dbt`/`uv` invocation through one shared `_run()` helper, so `.env`
  loading and dbt project/profile path resolution happen in exactly one
  place instead of being repeated per command.
- `invoke results` (with a `--csv` flag): reads
  `mart_recent_registrations_by_state` directly from SQLite and either
  prints it as a formatted table or writes it to a CSV in the repo root.
- Structured logging (stdlib `logging`) across `client.py`, `write.py`, and
  `__main__.py`, including a `before_sleep_log` hook on the `tenacity` retry
  loop.
- `mypy --strict` type checking across `src/`, `tests/`, and `tasks.py`.
- A full `pytest` suite (`tests/`): unit tests for `client`, `config`,
  `write`, and `__main__`'s exception propagation, plus a dedicated
  `tasks.py` test module and one opt-in live-API integration test (run via
  `pytest -m integration`). Enforces `--cov-fail-under=80` against
  `src/randomuser_elt` (currently 100%).
- `README.md` rewritten: a pipeline diagram, and clearly separated
  one-time-setup vs. run-repeatedly command sections, a results/viewing
  guide, and an ASCII project-layout tree.

### Changed

- Renamed the `src/extract` package to `src/randomuser_elt` to match the
  project name and the `[project.scripts]` entry point.
- Renamed `src/randomuser_elt/main.py` to `__main__.py` to match the
  `randomuser_elt.__main__:main` entry point declared in `pyproject.toml`.

### Fixed

- `dbt clean` reporting every target as "outside the project": caused by a
  relative `DBT_PROJECT_DIR`, which dbt's clean-target check compares
  against a resolved absolute path. `_run()` now resolves and exports
  `DBT_PROJECT_DIR`/`DBT_PROFILES_DIR` as absolute paths for every task.
- `invoke extract` silently doing nothing: a stale, real, exported shell
  environment variable was overriding `.env`'s value (dotenv is the lowest
  precedence source for `pydantic-settings`). Fixed by routing `extract()`
  through `_run()`, which always re-sources `.env`.
- A `unique` schema test on `email` that was factually wrong (the seed
  legitimately contains distinct people who share an email) — dropped,
  keeping `not_null`.
- Non-deterministic ordering in `dim_user`'s surrogate key generation on
  `email` ties — added `dob_date` as a tiebreaker.
- `tasks.py`'s automatic `dbt/data/` bootstrap running ahead of `dbt clean`,
  which has no reason to create state it doesn't touch — added an
  `ensure_db_dir` opt-out, used only by `clean`.
- Test isolation gaps where ambient environment variables (e.g. from an
  IDE's `python.envFile`) leaked into test assertions — `tests/conftest.py`
  now explicitly clears optional vars and sets defaults for required ones,
  rather than trusting whatever the shell happens to have set.

### Removed

- `mart_user_directory` and its `invoke results --directory` flag, to keep
  the presentation layer scoped to the one requested report.
- `docs/` from version control — design notes and review docs are kept
  locally but are no longer tracked, since the code and its tests are the
  source of truth.
