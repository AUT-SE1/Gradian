"""Structured JSON logging (DES-XC-01).

Tokens and passwords are never logged on purpose, and the formatter also scrubs anything that
looks like a bearer token or JWT, so one careless log call cannot leak a credential.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from common import context

_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")
_SENSITIVE_KEYS = {"password", "secret", "client_secret", "token", "access_token", "authorization"}
_STANDARD = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


def scrub(text: str) -> str:
    return _JWT.sub("[redacted]", _BEARER.sub("Bearer [redacted]", text))


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = context.request_id.get()
        record.sub = context.user_sub.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub(record.getMessage()),
            "request_id": getattr(record, "request_id", context.request_id.get()),
            "sub": getattr(record, "sub", context.user_sub.get()),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD or key in payload or key.startswith("_"):
                continue
            payload[key] = "[redacted]" if key.lower() in _SENSITIVE_KEYS else _clean(value)
        if record.exc_info:
            payload["exception"] = scrub(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def _clean(value: object) -> object:
    return scrub(value) if isinstance(value, str) else value
