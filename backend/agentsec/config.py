from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTSEC_", env_file=".env", extra="ignore")

    app_name: str = "AgentSec Inspector"
    version: str = "1.3.0"
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1024, le=65535)
    data_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("LOCALAPPDATA", ".")) / "AgentSec"
    )
    database_url: str | None = None
    api_token: str | None = None
    allowed_origins: str = (
        "http://tauri.localhost,tauri://localhost,"
        "http://localhost:1420,http://127.0.0.1:1420"
    )
    log_level: str = "INFO"
    max_response_bytes: int = 2_000_000
    request_timeout_seconds: float = 30.0
    allow_private_remote_targets: bool = False

    @property
    def db_url(self) -> str:
        return self.database_url or f"sqlite:///{self.data_dir / 'agentsec.db'}"

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    def prepare(self) -> None:
        for name in ("logs", "reports", "evidence", "backups"):
            (self.data_dir / name).mkdir(parents=True, exist_ok=True)
        if not self.api_token:
            token_file = self.data_dir / ".api-token"
            if token_file.exists():
                self.api_token = token_file.read_text(encoding="utf-8").strip()
            else:
                self.api_token = secrets.token_urlsafe(32)
                token_file.write_text(self.api_token, encoding="utf-8")
                try:
                    token_file.chmod(0o600)
                except OSError:
                    pass


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.prepare()
    return settings
