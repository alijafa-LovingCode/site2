from __future__ import annotations

import logging
import re
import sys

_SECRET_PATTERNS = [
    re.compile(r"(password\"?\s*[:=]\s*\"?)([^\",\s]+)", re.IGNORECASE),
    re.compile(r"(token\"?\s*[:=]\s*\"?)([^\",\s]+)", re.IGNORECASE),
    re.compile(r"(api_key\"?\s*[:=]\s*\"?)([^\",\s]+)", re.IGNORECASE),
    re.compile(r"(secret\"?\s*[:=]\s*\"?)([^\",\s]+)", re.IGNORECASE),
]


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        redacted = msg
        for pattern in _SECRET_PATTERNS:
            redacted = pattern.sub(r"\1***REDACTED***", redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RedactSecretsFilter())

    root.handlers.clear()
    root.addHandler(handler)

    # Keep third-party noise down
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
