from __future__ import annotations

import logging
import logging.handlers

import structlog

from .config import Settings


def configure_logging(settings: Settings) -> None:
    handler = logging.handlers.RotatingFileHandler(
        settings.data_dir / "logs" / "agentsec.jsonl",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logging.basicConfig(level=settings.log_level, handlers=[handler, logging.StreamHandler()])
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
