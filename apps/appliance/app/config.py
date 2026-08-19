"""Runtime configuration, read from the environment."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")

    ollama_url: str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_URL")
    # Why: no default. Silently picking a vision model would mean the operator
    # cannot tell which model produced a given financial record.
    ollama_vision_model: str = Field(alias="OLLAMA_VISION_MODEL")
    ollama_timeout_seconds: float = Field(default=180.0, alias="OLLAMA_TIMEOUT_SECONDS")

    data_root: Path = Field(default=Path("/data"), alias="DATA_ROOT")

    watch_enabled: bool = Field(default=True, alias="WATCH_ENABLED")
    watch_interval_seconds: float = Field(default=5.0, alias="WATCH_INTERVAL_SECONDS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("ollama_vision_model")
    @classmethod
    def _model_must_be_set(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "OLLAMA_VISION_MODEL is empty. Set it to the local model you want to "
                "use and run `ollama pull <model>` on the host first."
            )
        return value.strip()

    @property
    def inbox_dir(self) -> Path:
        return self.data_root / "inbox"

    @property
    def archive_dir(self) -> Path:
        return self.data_root / "archive"

    @property
    def review_dir(self) -> Path:
        return self.data_root / "review"

    def ensure_dirs(self) -> None:
        for directory in (self.inbox_dir, self.archive_dir, self.review_dir):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
