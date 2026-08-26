"""Invoke tasks for the randomuser_elt project."""

import csv as csv_lib
import shlex
import sqlite3
import subprocess
from pathlib import Path

from invoke import Context, task

from randomuser_elt.config import load_dbt_settings

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"
# Mirrors profiles.yml's schemas_and_paths.main -- not exposed via DbtSettings,
# since that only covers where dbt_project.yml/profiles.yml themselves live.
DB_PATH = ROOT / "dbt" / "data" / "randomuser.db"
DEFAULT_RESULT_TABLE = "mart_recent_registrations_by_state"
DIRECTORY_RESULT_TABLE = "mart_user_directory"


def _run(args: list[str], *, ensure_db_dir: bool = True) -> None:
    """Run *args* from the repo root with ``.env`` auto-loaded; stream output, raise on failure."""
    if ensure_db_dir:
        # dbt/data/ holds nothing but the gitignored .db file, so a fresh clone never has it
        # on disk -- sqlite3.connect() doesn't create missing parent directories, so without
        # this the first dbt command any task runs fails with "unable to open database file".
        # Skipped for `clean`, which has no reason to create state it doesn't touch.
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    dbt_settings = load_dbt_settings()
    project_dir = shlex.quote(str((ROOT / dbt_settings.project_dir).resolve()))
    profiles_dir = shlex.quote(str((ROOT / dbt_settings.profiles_dir).resolve()))
    env_file = shlex.quote(str(ENV_FILE))
    prefix = (
        f"set -a; [ -f {env_file} ] && . {env_file}; set +a; "
        # dbt clean compares DBT_PROJECT_DIR against resolved absolute paths, so a relative
        # value (as set in .env) makes it wrongly flag clean-targets as "outside the project".
        f"export DBT_PROJECT_DIR={project_dir} DBT_PROFILES_DIR={profiles_dir}; "
    )
    subprocess.run(["bash", "-c", prefix + shlex.join(args)], cwd=ROOT, check=True)


@task
def extract(c: Context) -> None:
    """Fetch the RandomUser CSV and write it to the dbt seed directory."""
    _run(["uv", "run", "randomuser_elt"])


@task
def parse(c: Context) -> None:
    """dbt parse — offline manifest/compile check (no warehouse connection)."""
    _run(["uv", "run", "dbt", "parse"])


@task
def debug(c: Context) -> None:
    """dbt debug — validate profile, project config, and adapter connection."""
    _run(["uv", "run", "dbt", "debug"])


@task
def deps(c: Context) -> None:
    """dbt deps — install packages declared in packages.yml (no-op until one exists)."""
    _run(["uv", "run", "dbt", "deps"])


@task(help={"full_refresh": "Fully rebuild the seed (drop + recreate)."})
def seed(c: Context, full_refresh: bool = False) -> None:
    """dbt seed — load CSV seeds into the SQLite database."""
    _run(["uv", "run", "dbt", "seed", *(["--full-refresh"] if full_refresh else [])])


@task
def clean(c: Context) -> None:
    """dbt clean — remove target/, dbt_packages/, and logs/."""
    _run(["uv", "run", "dbt", "clean"], ensure_db_dir=False)


@task
def build(c: Context) -> None:
    """dbt build — run models and tests together, in DAG order."""
    _run(["uv", "run", "dbt", "build"])


@task
def reset_db(c: Context) -> None:
    """Delete the SQLite database file so the next seed/build starts completely fresh."""
    DB_PATH.unlink(missing_ok=True)


@task(
    help={
        "directory": "Show mart_user_directory instead of the default recent-registrations report.",
        "csv": "Write the report to <table>.csv in the repo root instead of printing it.",
    }
)
def results(c: Context, directory: bool = False, csv: bool = False) -> None:
    """Print one presentation-layer mart (run `invoke build` first)."""
    table = DIRECTORY_RESULT_TABLE if directory else DEFAULT_RESULT_TABLE

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(f"select * from {table}").fetchall()
    connection.close()

    if csv:
        csv_path = ROOT / f"{table}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv_lib.writer(f)
            if rows:
                writer.writerow(rows[0].keys())
                writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {csv_path}")
        return

    print(f"\n=== {table} ({len(rows)} rows) ===")
    if not rows:
        print("(no rows)")
        return
    headers = rows[0].keys()
    widths = [max(len(h), *(len(str(row[h])) for row in rows)) for h in headers]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    for row in rows:
        cells = [str(row[h]) for h in headers]
        print("  ".join(c.ljust(w) for c, w in zip(cells, widths, strict=True)))
