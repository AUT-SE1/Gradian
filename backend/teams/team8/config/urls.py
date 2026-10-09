from core import views
from django.urls import include, path

urlpatterns = [
    path("health", views.health),
    path("auth/", include("gradian_auth.oidc_urls")),
    path("app", views.app),
    path("staff", views.staff),
    path("", views.index),
]
