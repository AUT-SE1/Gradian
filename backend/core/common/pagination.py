from rest_framework.pagination import LimitOffsetPagination as _LimitOffsetPagination


class LimitOffsetPagination(_LimitOffsetPagination):
    """`limit` and `offset` query parameters (DES-API-01)."""

    default_limit = 50
    max_limit = 200
