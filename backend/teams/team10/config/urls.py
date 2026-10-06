from django.urls import path

from core import views

# Reached through the core gateway: /api/teams/<n>/<path> arrives here as /<path>.
urlpatterns = [
    path("", views.index),
]
