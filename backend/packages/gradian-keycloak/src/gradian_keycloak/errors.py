class KeycloakError(Exception):
    """A Keycloak call failed. `status` is the HTTP status, or None if it was unreachable."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
