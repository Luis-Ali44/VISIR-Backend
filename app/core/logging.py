import logging
import sys
from collections.abc import Callable
from typing import Any

import structlog

from app.core.config import settings


def configurar_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    procesadores_base: list[Callable[..., Any]] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    procesadores_finales: list[Callable[..., Any]]

    if settings.environment == "development":
        procesadores_finales = [
            *procesadores_base,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        procesadores_finales = [
            *procesadores_base,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=procesadores_finales,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "rag_fiscal") -> logging.Logger:
    return logging.getLogger(name)
