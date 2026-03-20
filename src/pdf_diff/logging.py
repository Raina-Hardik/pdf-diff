from __future__ import annotations

import logging

import structlog

_configured = False


def configure_logging() -> None:
    global _configured

    if _configured:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger("pdf_diff")
