"""One error shape for every endpoint of every Gradian service (DES-API-01).

The body is `{"code", "message", "details"}`. Codes are stable English strings and messages are
Persian (DES-XC-03). Raise a subclass of `ApiError` for an error of your own and register its
message with `register_messages`.
"""

from collections.abc import Mapping
from typing import Any

MESSAGES: dict[str, str] = {
    "not_authenticated": "برای ادامه باید وارد سامانه شوید.",
    "authentication_failed": "احراز هویت ناموفق بود.",
    "invalid_token": "نشانه ورود نامعتبر یا منقضی است. دوباره وارد شوید.",
    "invalid_login": "ورود کامل نشد. دوباره تلاش کنید.",
    "permission_denied": "شما اجازه دسترسی به این بخش را ندارید.",
    "ambiguous_role": "برای حساب شما بیش از یک نقش تعریف شده است.",
    "incomplete_identity": "اطلاعات هویتی حساب شما کامل نیست.",
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


def register_messages(messages: Mapping[str, str]) -> None:
    """Add the Persian messages of a service's own error codes.

    Registering the same text again is harmless (modules can be imported twice by the reloader);
    a different text for an existing code is refused so two services cannot disagree silently.
    """
    for code, text in messages.items():
        existing = MESSAGES.get(code)
        if existing is not None and existing != text:
            raise ValueError(f"error code {code!r} already has a different message")
        MESSAGES[code] = text


def message_for(code: str) -> str:
    return MESSAGES.get(code, MESSAGES["server_error"])


def error_body(code: str, details: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message_for(code), "details": details or {}}


class ApiError(Exception):
    """Base of our own errors. Subclasses set `status_code` and `default_code`."""

    status_code = 500
    default_code = "server_error"

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(self.default_code)
        self.details: dict[str, Any] = details or {}

    @property
    def message(self) -> str:
        return message_for(self.default_code)

    def body(self) -> dict[str, Any]:
        return error_body(self.default_code, self.details)


class NotAuthenticatedError(ApiError):
    status_code = 401
    default_code = "not_authenticated"


class InvalidTokenError(ApiError):
    status_code = 401
    default_code = "invalid_token"


class InvalidLoginError(ApiError):
    """The browser sign-in on a group's pages could not be completed."""

    status_code = 400
    default_code = "invalid_login"


class PermissionDeniedError(ApiError):
    status_code = 403
    default_code = "permission_denied"


class AmbiguousRoleError(ApiError):
    status_code = 403
    default_code = "ambiguous_role"


class IncompleteIdentityError(ApiError):
    status_code = 403
    default_code = "incomplete_identity"


class IdentityProviderUnavailableError(ApiError):
    status_code = 502
    default_code = "identity_provider_unavailable"
