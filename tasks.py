"""Invoke tasks for the randomuser_elt project."""

import shlex
import subprocess
from pathlib import Path

from invoke import Context, task

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"
DBT_DIR = ROOT / "dbt"


def _run(args: list[str]) -> None:
    """Run *args* from the repo root with ``.env`` auto-loaded; stream output, raise on failure."""
    env_file = shlex.quote(str(ENV_FILE))
    dbt_dir = shlex.quote(str(DBT_DIR))
    prefix = (
        f"set -a; [ -f {env_file} ] && . {env_file}; set +a; "
        # dbt clean compares DBT_PROJECT_DIR against resolved absolute paths, so a relative
        # value (as set in .env) makes it wrongly flag clean-targets as "outside the project".
        f"export DBT_PROJECT_DIR={dbt_dir} DBT_PROFILES_DIR={dbt_dir}; "
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
    _run(["uv", "run", "dbt", "clean"])


@task
def build(c: Context) -> None:
    """dbt build — run models and tests together, in DAG order."""
    _run(["uv", "run", "dbt", "build"])
