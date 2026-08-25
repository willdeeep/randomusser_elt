"""Invoke tasks for the randomuser_elt project."""

import shlex
import subprocess
from pathlib import Path

from invoke import Context, task

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"


def _run(args: list[str]) -> None:
    """Run *args* from the repo root with ``.env`` auto-loaded; stream output, raise on failure."""
    env_file = shlex.quote(str(ENV_FILE))
    prefix = f"set -a; [ -f {env_file} ] && . {env_file}; set +a; "
    subprocess.run(["bash", "-c", prefix + shlex.join(args)], cwd=ROOT, check=True)


@task
def extract(c: Context) -> None:
    """Fetch the RandomUser CSV and write it to the dbt seed directory."""
    subprocess.run(["uv", "run", "randomuser_elt"], check=True)


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
