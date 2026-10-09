"""Per-request values that log records pick up automatically."""

from contextvars import ContextVar

from gradian_auth.context import user_sub

__all__ = ["request_id", "user_sub"]

request_id: ContextVar[str] = ContextVar("request_id", default="-")
