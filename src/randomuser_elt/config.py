"""Runtime configuration loaded from the environment.

Single source of truth for runtime config. No secrets are hard-coded; values
come from local .env variables. See ``.env.example``.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractSettings(BaseSettings):
    """Extract runtime configuration.

    Populated from environment variables prefixed with ``EXTRACT_``. Fields with a
    ``None`` default are optional source API params: when unset, the client omits
    that param from the request rather than sending an empty/placeholder value.
    """

    model_config = SettingsConfigDict(
        env_prefix="EXTRACT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Source Randomuser URL ---
    source_url: str = Field(
        description="Randomuser.me get request endpoint.",
    )
    source_format: str = Field(
        default="csv",
        description="Format of records returned by source API.",
    )
    source_results: int | None = Field(
        default=None,
        description="Number of results returned by source API. Omitted from params if unset.",
    )
    source_seed: str | None = Field(
        default=None,
        description="Seed to return repeatable results. Omitted from params if unset.",
    )
    source_nat: str | list[str] | None = Field(
        default=None,
        description="Nationality filter for results. Omitted from params if unset.",
    )
    source_inc: str | list[str] | None = Field(
        default=None,
        description="Included data columns/fields to return for each result. Omitted if unset.",
    )


class DbtSettings(BaseSettings):
    """dbt runtime configuration.

    Populated from environment variables prefixed with ``DBT_``.
    """

    model_config = SettingsConfigDict(
        env_prefix="DBT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    profiles_dir: Path = Field(
        description="Directory containing profiles.yml, applied so dbt runs from the project root.",
    )
    project_dir: Path = Field(
        description="Directory containing dbt_project.yml, applied so dbt runs from project root.",
    )


def load_extract_settings() -> ExtractSettings:
    """Construct :class:`ExtractSettings` from the environment."""
    return ExtractSettings()  # type: ignore[call-arg]


def load_dbt_settings() -> DbtSettings:
    """Construct :class:`DbtSettings` from the environment."""
    return DbtSettings()  # type: ignore[call-arg]
