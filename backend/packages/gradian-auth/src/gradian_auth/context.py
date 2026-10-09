"""Per-request values that log records pick up automatically."""

from contextvars import ContextVar

user_sub: ContextVar[str] = ContextVar("user_sub", default="-")
