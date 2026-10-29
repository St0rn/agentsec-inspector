from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False, "timeout": 30}
    if settings.db_url.startswith("sqlite")
    else {},
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection: object, _record: object) -> None:
    if settings.db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[Session, None]:
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)


def migrate_db() -> None:
    from alembic import command
    from alembic.config import Config

    if getattr(sys, "frozen", False):
        migration_root = Path(sys._MEIPASS) / "migrations"  # type: ignore[attr-defined]
    else:
        migration_root = Path(__file__).parents[1] / "migrations"
    if not migration_root.is_dir():
        raise RuntimeError(f"Database migrations are missing: {migration_root}")
    config = Config()
    config.set_main_option("script_location", str(migration_root))
    config.set_main_option("sqlalchemy.url", settings.db_url.replace("%", "%%"))
    command.upgrade(config, "head")
