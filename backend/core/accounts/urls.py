from django.urls import path

from accounts import views

urlpatterns = [
    path("auth/config", views.AuthConfigView.as_view(), name="auth-config"),
    path("me", views.MeView.as_view(), name="me"),
]
