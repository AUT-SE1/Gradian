"""Errors of the Core Service's own account handling. Codes are stable (DES-API-01).

The errors every service shares (invalid token, ambiguous role, ...) live in `gradian_auth.errors`.
"""

from gradian_auth.errors import ApiError, register_messages

register_messages(
    {
        "self_modification_forbidden": "مدیر نمی‌تواند نقش یا وضعیت حساب خودش را تغییر دهد.",
        "account_disabled": "حساب کاربری شما غیرفعال است.",
        "identity_conflict": "این اطلاعات قبلاً برای حساب دیگری ثبت شده است.",
    }
)


class AccountDisabledError(ApiError):
    status_code = 403
    default_code = "account_disabled"


class IdentityConflictError(ApiError):
    status_code = 409
    default_code = "identity_conflict"


class SelfModificationError(ApiError):
    status_code = 403
    default_code = "self_modification_forbidden"
