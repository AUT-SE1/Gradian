"""JSON versions of Django's 404 and 500 pages, so every response has the same error shape."""

from django.http import HttpRequest, JsonResponse

from common.exceptions import error_body


def not_found(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    return JsonResponse(error_body("not_found"), status=404)


def server_error(request: HttpRequest) -> JsonResponse:
    return JsonResponse(error_body("server_error"), status=500)
