"""The sign-in URLs of a group's pages: `path("auth/", include("gradian_auth.oidc_urls"))`."""

from django.urls import path

from gradian_auth import oidc

urlpatterns = [
    path("login", oidc.login, name="gradian-login"),
    path("callback", oidc.callback, name="gradian-callback"),
    path("logout", oidc.logout, name="gradian-logout"),
]
