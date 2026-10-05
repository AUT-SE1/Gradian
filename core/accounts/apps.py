from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self) -> None:
        from accounts import schema  # noqa: F401  (registers the OpenAPI security scheme)
