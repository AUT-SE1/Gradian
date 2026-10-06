"""Request id, user sub and one access-log line per request."""

import logging
import re
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from common import context

logger = logging.getLogger("gradian.access")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class RequestContextMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get("X-Request-ID", "")
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        rid_token = context.request_id.set(rid)
        sub_token = context.user_sub.set("-")
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = rid
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 1),
                },
            )
            return response
        finally:
            context.request_id.reset(rid_token)
            context.user_sub.reset(sub_token)
