"""Per-request values that log records pick up automatically."""

from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")
user_sub: ContextVar[str] = ContextVar("user_sub", default="-")
