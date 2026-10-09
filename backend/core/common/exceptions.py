"""One error shape for every endpoint (DES-API-01): {"code", "message", "details"}.

Codes are stable English strings; messages are Persian (DES-XC-03).
"""

from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

MESSAGES: dict[str, str] = {
    "not_authenticated": "برای ادامه باید وارد سامانه شوید.",
    "authentication_failed": "احراز هویت ناموفق بود.",
    "invalid_token": "نشانه ورود نامعتبر یا منقضی است. دوباره وارد شوید.",
    "permission_denied": "شما اجازه دسترسی به این بخش را ندارید.",
    "ambiguous_role": "برای حساب شما بیش از یک نقش تعریف شده است.",
    "self_modification_forbidden": "مدیر نمی‌تواند نقش یا وضعیت حساب خودش را تغییر دهد.",
    "account_disabled": "حساب کاربری شما غیرفعال است.",
    "incomplete_identity": "اطلاعات هویتی حساب شما کامل نیست.",
    "identity_conflict": "این اطلاعات قبلاً برای حساب دیگری ثبت شده است.",
    "identity_provider_unavailable": "سرویس احراز هویت در دسترس نیست. کمی بعد دوباره تلاش کنید.",
    "validation_error": "داده‌های ارسال‌شده نامعتبر است.",
    "not_found": "مورد درخواستی پیدا نشد.",
    "method_not_allowed": "این روش درخواست برای این آدرس مجاز نیست.",
    "parse_error": "قالب درخواست نامعتبر است.",
    "unsupported_media_type": "نوع محتوای درخواست پشتیبانی نمی‌شود.",
    "not_acceptable": "قالب پاسخ درخواستی پشتیبانی نمی‌شود.",
    "throttled": "تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.",
    "server_error": "خطای داخلی سرور رخ داد.",
}


def message_for(code: str) -> str:
    return MESSAGES.get(code, MESSAGES["server_error"])


class ApiError(APIException):
    """Base for our own errors. Subclasses set `status_code` and `default_code`."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(detail=message_for(self.default_code), code=self.default_code)
        self.details: dict[str, Any] = details or {}


def error_body(code: str, details: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message_for(code), "details": details or {}}


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    # Imported here: rest_framework.views resolves the default authentication class at import
    # time, which would import this module again while it is half loaded.
    from rest_framework.views import exception_handler as drf_exception_handler

    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.messages)
    elif isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: handler500 renders the same shape

    details: Any = {}
    if isinstance(exc, ApiError):
        code, details = exc.default_code, exc.details
    elif isinstance(exc, ValidationError):
        code, details = "validation_error", response.data
    elif isinstance(exc, APIException):
        codes = exc.get_codes()
        code = codes if isinstance(codes, str) else exc.default_code
        wait = getattr(exc, "wait", None)
        if wait is not None:
            details = {"retry_after_seconds": int(wait)}
    else:  # pragma: no cover - every exception drf_exception_handler answers is one of the above
        code = "server_error"
    if code not in MESSAGES:
        code = {
            status.HTTP_401_UNAUTHORIZED: "authentication_failed",
            status.HTTP_403_FORBIDDEN: "permission_denied",
        }.get(response.status_code, "server_error")
    response.data = error_body(code, details)
    return response
