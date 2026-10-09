"""Errors raised while identifying a caller. Codes are stable (DES-API-01)."""

from rest_framework import status

from common.exceptions import ApiError


class AmbiguousRoleError(ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "ambiguous_role"


class AccountDisabledError(ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "account_disabled"


class IncompleteIdentityError(ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "incomplete_identity"


class IdentityConflictError(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "identity_conflict"


class IdentityProviderUnavailableError(ApiError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "identity_provider_unavailable"


class SelfModificationError(ApiError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "self_modification_forbidden"
