"""Unit tests for tasks.py.

tasks.py lives at the repo root, not under src/, but is importable as a plain
module when pytest is run as ``python -m pytest`` from the repo root (which
puts the repo root on sys.path). invoke's @task decorator wraps each function
in an invoke.tasks.Task, which still requires a real invoke.Context as its
first argument (a MagicMock fails invoke's own isinstance check) but otherwise
calls straight through to the original function body -- so tasks are called
directly here rather than via invoke's CLI runner.
"""

import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import tasks
from invoke import Context

from randomuser_elt.config import DbtSettings

CTX = Context()


@pytest.fixture(autouse=True)
def _mock_dbt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run() calls the real load_dbt_settings() unless a test overrides it;
    stub it here so every test in this file is isolated from .env by default."""
    settings = DbtSettings(_env_file=None, profiles_dir=Path("dbt"), project_dir=Path("dbt"))  # type: ignore[call-arg]
    monkeypatch.setattr(tasks, "load_dbt_settings", lambda: settings)


@pytest.fixture
def _no_real_subprocess(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_run = MagicMock()
    monkeypatch.setattr("tasks.subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def _isolated_db_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Points tasks.DB_PATH at a tmp_path location, so tests touching it never
    risk the real project's dbt/data/randomuser.db."""
    db_path = tmp_path / "dbt" / "data" / "randomuser.db"
    monkeypatch.setattr(tasks, "DB_PATH", db_path)
    return db_path


def test_run_passes_command_through_to_subprocess(
    _no_real_subprocess: MagicMock, _isolated_db_path: Path
) -> None:
    tasks._run(["echo", "hello world"])

    args = _no_real_subprocess.call_args.args[0]
    assert args[:2] == ["bash", "-c"]
    assert "echo 'hello world'" in args[2]


def test_run_resolves_dbt_dirs_to_absolute_paths(
    _no_real_subprocess: MagicMock, _isolated_db_path: Path
) -> None:
    tasks._run(["dbt", "clean"])

    command = _no_real_subprocess.call_args.args[0][2]
    absolute_dbt_dir = str(tasks.ROOT / "dbt")
    assert f"DBT_PROJECT_DIR={absolute_dbt_dir}" in command
    assert f"DBT_PROFILES_DIR={absolute_dbt_dir}" in command


def test_run_creates_db_directory_by_default(
    _no_real_subprocess: MagicMock, _isolated_db_path: Path
) -> None:
    assert not _isolated_db_path.parent.exists()

    tasks._run(["echo", "hi"])

    assert _isolated_db_path.parent.is_dir()


def test_run_skips_db_directory_when_disabled(
    _no_real_subprocess: MagicMock, _isolated_db_path: Path
) -> None:
    tasks._run(["echo", "hi"], ensure_db_dir=False)

    assert not _isolated_db_path.parent.exists()


def test_run_propagates_subprocess_failure(
    _no_real_subprocess: MagicMock, _isolated_db_path: Path
) -> None:
    _no_real_subprocess.side_effect = subprocess.CalledProcessError(1, ["bash"])

    with pytest.raises(subprocess.CalledProcessError):
        tasks._run(["false"])


def test_extract_runs_the_console_script(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    monkeypatch.setattr(tasks, "_run", mock_run)

    tasks.extract(CTX)

    mock_run.assert_called_once_with(["uv", "run", "randomuser_elt"])


@pytest.mark.parametrize(
    ("task_name", "expected_args"),
    [
        ("parse", ["uv", "run", "dbt", "parse"]),
        ("debug", ["uv", "run", "dbt", "debug"]),
        ("deps", ["uv", "run", "dbt", "deps"]),
        ("build", ["uv", "run", "dbt", "build"]),
    ],
)
def test_simple_dbt_tasks_run_the_expected_command(
    monkeypatch: pytest.MonkeyPatch, task_name: str, expected_args: list[str]
) -> None:
    mock_run = MagicMock()
    monkeypatch.setattr(tasks, "_run", mock_run)

    getattr(tasks, task_name)(CTX)

    mock_run.assert_called_once_with(expected_args)


def test_seed_without_full_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    monkeypatch.setattr(tasks, "_run", mock_run)

    tasks.seed(CTX)

    mock_run.assert_called_once_with(["uv", "run", "dbt", "seed"])


def test_seed_with_full_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    monkeypatch.setattr(tasks, "_run", mock_run)

    tasks.seed(CTX, full_refresh=True)

    mock_run.assert_called_once_with(["uv", "run", "dbt", "seed", "--full-refresh"])


def test_clean_disables_db_directory_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_run = MagicMock()
    monkeypatch.setattr(tasks, "_run", mock_run)

    tasks.clean(CTX)

    mock_run.assert_called_once_with(["uv", "run", "dbt", "clean"], ensure_db_dir=False)


def test_reset_db_deletes_the_database_file(_isolated_db_path: Path) -> None:
    _isolated_db_path.parent.mkdir(parents=True)
    _isolated_db_path.write_text("not a real db")

    tasks.reset_db(CTX)

    assert not _isolated_db_path.exists()


def test_reset_db_is_a_noop_when_file_already_missing(_isolated_db_path: Path) -> None:
    assert not _isolated_db_path.exists()

    tasks.reset_db(CTX)  # must not raise


@pytest.fixture
def _results_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(db_path)
    connection.execute("create table mart_recent_registrations_by_state (state text, name text)")
    connection.execute("insert into mart_recent_registrations_by_state values ('Ohio', 'Bob')")
    connection.execute("create table mart_user_directory (name text, age int)")
    connection.execute("insert into mart_user_directory values ('Alice', 30)")
    connection.commit()
    connection.close()
    monkeypatch.setattr(tasks, "DB_PATH", db_path)
    return db_path


def test_results_defaults_to_recent_registrations_report(
    _results_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tasks.results(CTX)

    out = capsys.readouterr().out
    assert "mart_recent_registrations_by_state" in out
    assert "Bob" in out
    assert "mart_user_directory" not in out
    assert "Alice" not in out


def test_results_directory_flag_switches_report(
    _results_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tasks.results(CTX, directory=True)

    out = capsys.readouterr().out
    assert "mart_user_directory" in out
    assert "Alice" in out
    assert "Bob" not in out


def test_results_reports_no_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "empty.db"
    connection = sqlite3.connect(db_path)
    connection.execute("create table mart_recent_registrations_by_state (state text)")
    connection.commit()
    connection.close()
    monkeypatch.setattr(tasks, "DB_PATH", db_path)

    tasks.results(CTX)

    assert "(no rows)" in capsys.readouterr().out


def test_results_csv_writes_file_instead_of_printing(
    _results_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(tasks, "ROOT", tmp_path)

    tasks.results(CTX, csv=True)

    csv_path = tmp_path / "mart_recent_registrations_by_state.csv"
    content = csv_path.read_text()
    assert "state,name" in content
    assert "Ohio,Bob" in content

    out = capsys.readouterr().out
    assert "Wrote 1 rows" in out
    assert "===" not in out
