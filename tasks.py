"""Invoke tasks for the randomuser_elt project."""

import subprocess

from invoke import Context, task


@task
def extract(c: Context) -> None:
    """Fetch the RandomUser CSV and write it to the dbt seed directory."""
    subprocess.run(["uv", "run", "randomuser_elt"], check=True)
